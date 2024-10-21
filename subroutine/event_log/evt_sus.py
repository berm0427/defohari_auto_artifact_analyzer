import xml.etree.ElementTree as ET
import csv
import re

# 안티포렌식 키워드 목록 (정규 표현식)
anti_forensic_keywords = [
    r'(?i).*ccleaner.*', r'(?i).*cleaner.*', r'(?i).*eraser.*',
    r'(?i).*wiper.*', r'(?i).*scrubber.*', r'(?i).*delete.*',
    r'(?i).*remove.*', r'(?i).*destroy.*', r'(?i).*bleachbit.*'
]

def read_cleaned_xml(file_path):
    """XML 파일을 읽고 특수 문자를 처리한 내용을 반환"""
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    # 특수 문자 처리
    cleaned_content = re.sub(r'&(?!amp;)', '&amp;', content)
    return cleaned_content

def evt_xml_file_to_csv(xml_file_path, csv_file_path):
    try:
        # XML 파일 파싱
        cleaned_xml = read_cleaned_xml(xml_file_path)
        root = ET.fromstring(cleaned_xml)

        # CSV 파일 작성
        with open(csv_file_path, 'w', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(['로그종류', '시간', '이벤트ID', '이벤트내용'])  # 헤더 작성

            # 각 이벤트를 순회
            for event in root.findall('Event'):
                log_type = event.find('로그종류').text
                time = event.find('시간').text
                event_id = event.find('이벤트ID').text
                event_content = event.find('이벤트내용').text

                # 안티포렌식 키워드가 포함된 이벤트만 추출
                if any(re.search(keyword, event_content) for keyword in anti_forensic_keywords):
                    writer.writerow([log_type, time, event_id, event_content])

        print(f"안티포렌식 이벤트 로그가 {csv_file_path}에 저장되었습니다.")

    except ET.ParseError as e:
        print(f"XML 파일을 파싱하는 중 오류가 발생했습니다: {e}")
    except FileNotFoundError as e:
        print(f"파일을 찾을 수 없습니다: {e}")
    except Exception as e:
        print(f"예기치 않은 오류가 발생했습니다: {e}")

# XML 파일 경로와 CSV 파일 경로 설정
xml_file_path = r'..\..\output\artifact\event_log\event_logs.xml'
csv_file_path = r'..\..\output\suspicious_artifact\event_log\anti_forensic_events.csv'

# XML 파일을 CSV로 변환
evt_xml_file_to_csv(xml_file_path, csv_file_path)
