import os
import csv
import xml.etree.ElementTree as ET
import re

def normalize_path(path):
    """경로를 정규화하여 비교를 쉽게 만듦"""
    return os.path.normpath(path).replace("\\", "/").lower()

def extract_lnk_name(file_path):
    """경로에서 .lnk 파일 이름만 추출"""
    return os.path.basename(file_path).lower()

def load_csv_data(file_path):
    """CSV 데이터를 로드하고 리스트로 반환"""
    data = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                row['file_name'] = extract_lnk_name(row['file_path'])
                data.append(row)
    except Exception as e:
        print(f"CSV 로드 오류: {e}")
    return data

def load_xml_data(file_path):
    """XML 데이터를 로드하고 리스트로 반환"""
    data = []
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        for lnk_file in root.findall('LnkFile'):
            file_data = {elem.tag: elem.text for elem in lnk_file}
            file_data['file_name'] = extract_lnk_name(file_data['file_path'])
            data.append(file_data)
    except Exception as e:
        print(f"XML 로드 오류: {e}")
    return data

def merge_data(time_data, path_data):
    """시간 정보와 경로 정보를 병합"""
    merged_data = []
    for path_item in path_data:
        lnk_name = path_item['file_name']
        matched_time = next((t for t in time_data if t['file_name'] == lnk_name), None)

        merged_item = path_item.copy()
        if matched_time:
            merged_item.update({
                "creation_time": matched_time.get("creation_time", "N/A"),
                "access_time": matched_time.get("access_time", "N/A"),
                "write_time": matched_time.get("write_time", "N/A")
            })
        else:
            print(f"경로 매칭 실패: {path_item['file_path']}")
        merged_data.append(merged_item)

    return merged_data

def save_csv(data, output_path):
    """CSV로 저장"""
    fieldnames = list(data[0].keys())
    try:
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        print(f"CSV 파일 저장 완료: {output_path}")
    except Exception as e:
        print(f"CSV 저장 오류: {e}")

def save_xml(data, output_path):
    """XML로 저장"""
    root = ET.Element('LnkFiles')
    for item in data:
        lnk_elem = ET.SubElement(root, 'LnkFile')
        for key, value in item.items():
            child = ET.SubElement(lnk_elem, key)
            child.text = value if value else 'N/A'

    tree = ET.ElementTree(root)
    try:
        with open(output_path, 'wb') as f:
            tree.write(f, encoding='utf-8', xml_declaration=True)
        print(f"XML 파일 저장 완료: {output_path}")
    except Exception as e:
        print(f"XML 저장 오류: {e}")

def find_files_in_directory(directory, pattern):
    """디렉토리에서 특정 패턴의 파일 찾기"""
    return [os.path.join(directory, f) for f in os.listdir(directory) if re.match(pattern, f)]

def process_files(directory):
    """모든 관련 파일을 찾고 병합한 후 원본 파일에 덮어쓰기"""
    time_csv_files = find_files_in_directory(directory, r'lnk_files_time_(.*)\.csv')
    path_csv_files = find_files_in_directory(directory, r'lnk_files_(.*)\.csv')

    for time_csv in time_csv_files:
        username = re.search(r'lnk_files_time_(.*)\.csv', os.path.basename(time_csv)).group(1)
        path_csv = os.path.join(directory, f'lnk_files_{username}.csv')

        if os.path.exists(path_csv):
            print(f"파일 병합 시작: {username}")
            time_data = load_csv_data(time_csv)
            path_data = load_csv_data(path_csv)

            merged_data = merge_data(time_data, path_data)
            save_csv(merged_data, path_csv)  # 기존 파일에 덮어쓰기

            # XML 파일 처리
            time_xml = os.path.join(directory, f'lnk_files_time_{username}.xml')
            path_xml = os.path.join(directory, f'lnk_files_{username}.xml')

            if os.path.exists(time_xml) and os.path.exists(path_xml):
                time_data_xml = load_xml_data(time_xml)
                path_data_xml = load_xml_data(path_xml)
                merged_data_xml = merge_data(time_data_xml, path_data_xml)
                save_xml(merged_data_xml, path_xml)  # 기존 파일에 덮어쓰기

def main():
    directory = os.path.normpath(os.path.join(os.path.dirname(__file__), "../../output/artifact/LNK"))
    print(f"===== {directory} 내 파일 병합 및 덮어쓰기 시작 =====")
    process_files(directory)
    print(f"===== 파일 병합 및 덮어쓰기 완료 =====")

if __name__ == "__main__":
    main()
