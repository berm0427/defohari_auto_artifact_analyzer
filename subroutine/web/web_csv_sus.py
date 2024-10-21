import xml.etree.ElementTree as ET
import csv
import chardet
import re


def detect_encoding(file_path):
    with open(file_path, 'rb') as file:
        raw_data = file.read()
        result = chardet.detect(raw_data)
        return result['encoding']


def read_cleaned_xml(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # 특수 문자 처리
    cleaned_content = re.sub(r'&(?!amp;)', '&amp;', content)
    return cleaned_content

"""
def tor_xml_to_csv(xml_file_path, csv_file_path):
    # 안티포렌식 키워드 목록 (함수 안에 포함)
    anti_forensic_keywords = [
        r'(?i).*ccleaner.*', r'(?i).*cleaner.*', r'(?i).*eraser.*',
        r'(?i).*wiper.*', r'(?i).*scrubber.*', r'(?i).*delete.*',
        r'(?i).*remove.*', r'(?i).*destroy.*', r'(?i).*bleachbit.*'
    ]

    try:
        # XML 파일 파싱
        tree = ET.parse(xml_file_path)
        root = tree.getroot()

        # CSV 파일 작성
        with open(csv_file_path, 'w', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file)

            # 헤더 작성
            writer.writerow(['Torrent Hash', 'Caption', 'Path', 'Added On', 'Completed On', 'Downloaded', 'Uploaded', 'Distributor or Downloader'])

            # 각 torrent 데이터를 CSV에 작성
            for torrent in root.findall('.//torrent'):
                torrent_hash = torrent.get('hash', '')
                caption = torrent.find('caption').text if torrent.find('caption') is not None else ''
                path = torrent.find('path').text if torrent.find('path') is not None else ''
                added_on = torrent.find('added_on').text if torrent.find('added_on') is not None else ''
                completed_on = torrent.find('completed_on').text if torrent.find('completed_on') is not None else ''
                downloaded = torrent.find('downloaded').text if torrent.find('downloaded') is not None else ''
                uploaded = torrent.find('uploaded').text if torrent.find('uploaded') is not None else ''
                created_torrent = torrent.find('created_torrent').text if torrent.find('created_torrent') is not None else ''

                # 안티포렌식 키워드 매칭 여부 확인
                if any(re.search(keyword, path.lower()) for keyword in anti_forensic_keywords):
                    # 매칭된 경우에만 CSV에 기록
                    writer.writerow([torrent_hash, caption, path, added_on, completed_on, downloaded, uploaded, created_torrent])

    except ET.ParseError as e:
        print(f"XML 파일을 파싱하는 중 오류가 발생했습니다: {e}")
    except FileNotFoundError as e:
        print(f"파일을 찾을 수 없습니다: {e}")
    except Exception as e:
        print(f"예기치 않은 오류가 발생했습니다: {e}")
"""

def his_xml_file_to_csv(xml_file_path, csv_file_path):
    try:
        # XML 파일 정리 및 파싱
        cleaned_xml = read_cleaned_xml(xml_file_path)
        root = ET.fromstring(cleaned_xml)

        # 안티포렌식 키워드 목록 (정규 표현식)
        anti_forensic_keywords = [
            r'(?i).*ccleaner.*', r'(?i).*cleaner.*', r'(?i).*eraser.*',
            r'(?i).*wiper.*', r'(?i).*scrubber.*', r'(?i).*delete.*',
            r'(?i).*remove.*', r'(?i).*destroy.*', r'(?i).*bleachbit.*'
        ]

        # CSV 파일 작성
        with open(csv_file_path, 'w', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file)

            # 헤더 작성
            writer.writerow(['URL', 'Visit Time'])

            # 각 방문 기록을 CSV에 작성
            for visit in root.findall('visit'):
                url = visit.find('url').text
                visit_time_element = visit.find('visit_time')
                visit_time = visit_time_element.text if visit_time_element is not None else ''

                # 정규 표현식을 사용하여 URL이 안티포렌식 키워드를 포함하는 경우만 처리
                if any(re.match(keyword, url) for keyword in anti_forensic_keywords):
                    writer.writerow([url, visit_time])

    except ET.ParseError as e:
        print(f"XML 파일을 파싱하는 중 오류가 발생했습니다: {e}")
    except FileNotFoundError as e:
        print(f"파일을 찾을 수 없습니다: {e}")
    except Exception as e:
        print(f"예기치 않은 오류가 발생했습니다: {e}")

# XML 파일 경로와 CSV 파일 경로 설정
his_xml_file_path = r'..\..\output\artifact\web\web_output.xml'
his_csv_file_path = r'..\..\output\suspicious_artifact\web\web_sus.csv'

"""
tor_output_xml = r"torrent_output.xml"
tor_csv_file_path = 'web_filtered.csv'
"""

# XML 파일을 CSV로 변환
his_xml_file_to_csv(his_xml_file_path, his_csv_file_path)
