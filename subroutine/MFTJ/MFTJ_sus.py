# -*- coding: utf-8 -*-
import pandas as pd
import re
import os
import logging
from lxml import etree as LET
from xml.sax.saxutils import escape

# 로깅 설정
logging.basicConfig(
    filename='filter_and_convert.log',
    level=logging.INFO,
    format='%(asctime)s:%(levelname)s:%(message)s'
)

# 안티포렌식 의심 키워드 리스트 (플래그 제거)
anti_forensic_keywords = [
    'ccleaner', 'cleaner', 'eraser',
    'wiper', 'scrubber', 'delete',
    'remove', 'destroy', 'bleachbit'
]

# 하나의 패턴으로 결합하고 대소문자 무시 플래그 적용
combined_pattern = re.compile('|'.join(anti_forensic_keywords), re.IGNORECASE)

def clean_text(text):
    """
    XML에서 허용되지 않는 제어 문자를 제거하고, 잘못된 CDATA 구문을 수정합니다.
    """
    if not isinstance(text, str):
        text = str(text)
    # XML 1.0에서 허용되지 않는 제어 문자 제거
    text = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F]', '', text)
    # 잘못된 CDATA 구문 제거
    text = text.replace('![CDATA[', '')
    return text

def sanitize_tag(tag):
    """
    XML 태그 이름을 유효하게 만듭니다.
    - 공백을 언더스코어로 대체
    - 알파벳, 숫자, 언더스코어만 남김
    - 숫자로 시작하면 언더스코어 추가
    """
    # 공백을 언더스코어로 대체
    tag = tag.replace(' ', '_')
    # 알파벳, 숫자, 언더스코어만 남김
    tag = re.sub(r'[^A-Za-z0-9_]', '', tag)
    # 숫자로 시작하면 언더스코어 추가
    if re.match(r'^[0-9]', tag):
        tag = '_' + tag
    return tag

def filter_csv(csv_file_path, filtered_csv_path, filter_columns, output_columns):
    """
    CSV 파일을 읽어 특정 열에서 안티포렌식 키워드를 포함하는 행을 필터링하고,
    지정된 출력 컬럼만 포함하여 새로운 CSV로 저장합니다.
    """
    try:
        # CSV 파일 읽기
        df = pd.read_csv(csv_file_path, encoding='utf-8', low_memory=False, on_bad_lines='skip', dtype=str)
        logging.info(f"'{csv_file_path}' 파일을 성공적으로 읽었습니다. 총 행 수: {len(df)}")
        print(f"'{csv_file_path}' 파일을 성공적으로 읽었습니다. 총 행 수: {len(df)}")
        
        # 존재하지 않는 필터링 열 확인
        missing_filter_cols = [col for col in filter_columns if col not in df.columns]
        if missing_filter_cols:
            logging.warning(f"'{csv_file_path}' 파일에 필터링할 열이 존재하지 않습니다: {missing_filter_cols}")
            print(f"'{csv_file_path}' 파일에 필터링할 열이 존재하지 않습니다: {missing_filter_cols}")
            return None
        
        # 존재하지 않는 출력 열 확인
        missing_output_cols = [col for col in output_columns if col not in df.columns]
        if missing_output_cols:
            logging.warning(f"'{csv_file_path}' 파일에 출력할 열이 존재하지 않습니다: {missing_output_cols}")
            print(f"'{csv_file_path}' 파일에 출력할 열이 존재하지 않습니다: {missing_output_cols}")
            return None
        
        # 필터링 전 데이터 샘플 출력
        logging.info(f"'{csv_file_path}' 파일의 필터링 전 샘플 데이터:")
        print(f"'{csv_file_path}' 파일의 필터링 전 샘플 데이터:")
        print(df[filter_columns].head(5))
        
        # 필터링 조건 생성 (정규 표현식 사용)
        mask = df[filter_columns].apply(
            lambda row: bool(combined_pattern.search(' '.join(row.dropna().astype(str)))),
            axis=1
        )
        
        # 필터링된 데이터프레임 생성
        filtered_df = df[mask]
        logging.info(f"필터링된 행 수: {len(filtered_df)}")
        print(f"필터링된 행 수: {len(filtered_df)}")
        
        if filtered_df.empty:
            logging.info(f"'{csv_file_path}' 파일에 필터링된 데이터가 없습니다.")
            print(f"'{csv_file_path}' 파일에 필터링된 데이터가 없습니다.")
            return None
        else:
            logging.info(f"'{csv_file_path}' 파일에 필터링된 데이터가 {len(filtered_df)}건 있습니다.")
            print(f"'{csv_file_path}' 파일에 필터링된 데이터가 {len(filtered_df)}건 있습니다.")
        
        # 출력에 필요한 컬럼만 선택
        filtered_df = filtered_df[output_columns]
        
        # 인코딩 이슈로 인해 NaN 값이 생길 수 있으므로 제거
        # filter_columns에 포함된 컬럼에만 NaN 제거를 적용
        existing_filter_cols = [col for col in filter_columns if col in filtered_df.columns]
        filtered_df_before_dropna = len(filtered_df)
        filtered_df.dropna(subset=existing_filter_cols, inplace=True)
        filtered_df_after_dropna = len(filtered_df)
        logging.info(f"NaN 값 제거 전: {filtered_df_before_dropna}건, 제거 후: {filtered_df_after_dropna}건")
        print(f"NaN 값 제거 전: {filtered_df_before_dropna}건, 제거 후: {filtered_df_after_dropna}건")
        
        if filtered_df.empty:
            logging.info(f"NaN 값 제거 후 '{filtered_csv_path}' 파일에 필터링된 데이터가 없습니다.")
            print(f"NaN 값 제거 후 '{filtered_csv_path}' 파일에 필터링된 데이터가 없습니다.")
            return None
        else:
            logging.info(f"'{csv_file_path}' 파일의 {filter_columns}에서 NaN을 제거한 후, {len(filtered_df)}건의 데이터가 남았습니다.")
            print(f"'{csv_file_path}' 파일의 {filter_columns}에서 NaN을 제거한 후, {len(filtered_df)}건의 데이터가 남았습니다.")
        
        # 필터링된 데이터 샘플 출력
        logging.info(f"'{filtered_csv_path}' 파일에 저장될 필터링된 데이터 샘플:")
        print(f"'{filtered_csv_path}' 파일에 저장될 필터링된 데이터 샘플:")
        print(filtered_df.head(5))
        
        # 필터링된 데이터를 새로운 CSV 파일로 저장
        filtered_df.to_csv(filtered_csv_path, index=False, encoding='utf-8')
        logging.info(f"'{csv_file_path}' 에서 필터링된 데이터가 '{filtered_csv_path}' 로 저장되었습니다.")
        print(f"'{csv_file_path}' 에서 필터링된 데이터가 '{filtered_csv_path}' 로 저장되었습니다.")
        
        return filtered_df
    except FileNotFoundError:
        logging.error(f"파일을 찾을 수 없습니다: {csv_file_path}")
        print(f"파일을 찾을 수 없습니다: {csv_file_path}")
        return None
    except pd.errors.ParserError as e:
        logging.error(f"CSV 파싱 중 오류가 발생했습니다: {e}")
        print(f"CSV 파싱 중 오류가 발생했습니다: {e}")
        return None
    except Exception as e:
        logging.error(f"파일 처리 중 오류가 발생했습니다: {e}")
        print(f"파일 처리 중 오류가 발생했습니다: {e}")
        return None

def pandas_csv_to_xml_lxml(df, xml_file_path, root_element_name="Root", record_element_name="Record"):
    """
    pandas DataFrame을 XML 파일로 변환하고, 가독성을 높이기 위해 들여쓰기를 적용합니다.
    """
    try:
        root = LET.Element(root_element_name)
        
        for index, row in df.iterrows():
            try:
                record = LET.SubElement(root, record_element_name)
                for field in df.columns:
                    sanitized_field = sanitize_tag(field)
                    elem = LET.SubElement(record, sanitized_field)
                    # XML에 유효하지 않은 문자를 이스케이프 처리하고, 제어 문자 제거
                    cleaned_text = clean_text(str(row[field])) if pd.notnull(row[field]) else ""
                    escaped_text = escape(cleaned_text)
                    # CDATA 섹션 제거하고 텍스트 직접 포함
                    elem.text = escaped_text
            except Exception as e:
                logging.error(f"레코드 {index} 처리 중 오류 발생: {e}")
                print(f"레코드 {index} 처리 중 오류 발생: {e}")
        
        # ElementTree 객체 생성
        tree = LET.ElementTree(root)
        
        # XML 파일로 저장 (pretty_print=True로 예쁘게)
        tree.write(xml_file_path, pretty_print=True, xml_declaration=True, encoding='utf-8')
        
        logging.info(f"'{xml_file_path}' 파일이 성공적으로 생성되었습니다.")
        print(f"'{xml_file_path}' 파일이 성공적으로 생성되었습니다.")
    except LET.XMLSyntaxError as e:
        logging.error(f"XML 구문 오류: {e}")
        print(f"XML 구문 오류: {e}")
    except Exception as e:
        logging.error(f"XML 변환 중 오류가 발생했습니다: {e}")
        print(f"XML 변환 중 오류가 발생했습니다: {e}")

def main():
    # 원본 CSV 파일 경로
    mft_output_csv = r'..\..\output\artifact\MFTJ\mft_output.csv'
    usn_output_csv = r'..\..\output\artifact\MFTJ\usn_output.csv'
    
    # 필터링된 CSV 파일 경로
    mft_filtered_csv = r'..\..\output\suspicious_artifact\MFTJ\mft_filtered.csv'
    usn_filtered_csv = r'..\..\output\suspicious_artifact\MFTJ\usn_filtered.csv'
    
    # 필터링에 사용할 열 이름 (안티포렌식 키워드 검색을 위한 열)
    mft_filter_columns = ['Filename']  # 필요 시 'Filepath' 추가
    usn_filter_columns = ['filename']
    
    # 출력에 포함할 열 이름 (파일 생성 시간과 파일 이름)
    mft_output_columns = [
        'SI Creation Time', 'SI Modification Time', 'SI Access Time', 'SI Entry Time',
        'FN Creation Time', 'FN Modification Time', 'FN Access Time', 'FN Entry Time',
        'Filename'
    ]  # 필요 시 'Filepath' 추가
    usn_output_columns = ['timestamp', 'filename']
    
    # MFT CSV 필터링
    mft_filtered_df = filter_csv(
        csv_file_path=mft_output_csv,
        filtered_csv_path=mft_filtered_csv,
        filter_columns=mft_filter_columns,
        output_columns=mft_output_columns
    )
    
    # USN CSV 필터링
    usn_filtered_df = filter_csv(
        csv_file_path=usn_output_csv,
        filtered_csv_path=usn_filtered_csv,
        filter_columns=usn_filter_columns,
        output_columns=usn_output_columns
    )

    # 필터링된 CSV를 XML로 변환
    # MFT 필터링된 데이터
    if mft_filtered_df is not None and not mft_filtered_df.empty:
        mft_xml_file = r'..\..\output\suspicious_artifact\MFTJ\mft_filtered.xml'
        pandas_csv_to_xml_lxml(
            df=mft_filtered_df,
            xml_file_path=mft_xml_file,
            root_element_name="MFTRecords",
            record_element_name="MFTRecord"
        )
    else:
        logging.info(f"'{mft_filtered_csv}' 파일에 필터링된 데이터가 없습니다. XML 변환을 건너뜁니다.")
        print(f"'{mft_filtered_csv}' 파일에 필터링된 데이터가 없습니다. XML 변환을 건너뜁니다.")
    
    # USN 필터링된 데이터
    if usn_filtered_df is not None and not usn_filtered_df.empty:
        usn_xml_file = r'..\..\output\suspicious_artifact\MFTJ\usn_filtered.xml'
        pandas_csv_to_xml_lxml(
            df=usn_filtered_df,
            xml_file_path=usn_xml_file,
            root_element_name="USNRecords",
            record_element_name="USNRecord"
        )
    else:
        logging.info(f"'{usn_filtered_csv}' 파일에 필터링된 데이터가 없습니다. XML 변환을 건너뜁니다.")
        print(f"'{usn_filtered_csv}' 파일에 필터링된 데이터가 없습니다. XML 변환을 건너뜁니다.")

if __name__ == "__main__":
    main()
