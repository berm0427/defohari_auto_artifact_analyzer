import os
import csv
import xml.etree.ElementTree as ET
import re
import subprocess

# 사용자 이름을 찾아 경로에서 치환할 수 있도록 동적 경로 생성
def update_user_path(file_path, username):
    r"""C:\Users\berm2 부분을 동적으로 C:\Users\{username}으로 교체"""
    return re.sub(r'C:\\Users\\[^\\]+', fr'C:\\Users\\{username}', file_path)

# 외부 스크립트에서 사용자 이름을 동적으로 가져오는 함수
def get_usernames_from_script(script_path):
    """외부 스크립트를 실행해 여러 사용자 이름을 가져오는 함수"""
    try:
        result = subprocess.run(['python', script_path], capture_output=True, text=True, check=True)
        usernames = []
        # 스크립트 출력에서 유효한 사용자 이름 파싱
        for line in result.stdout.splitlines():
            if "Found valid username" in line:
                # 사용자 이름 파싱
                username = line.split(":", 1)[1].strip()
                usernames.append(username)
        return usernames
    except subprocess.CalledProcessError as e:
        print(f"외부 스크립트 실행 중 오류 발생: {e}")
    return []

# 의심스러운 항목을 체크하는 함수
def is_suspicious(text):
    SUSPICIOUS_KEYWORDS = [
        'anti',
        'forensic',
        'eraser',
        'wiper',
        'scrubber',
        'delete',
        'remove',
        'destroy',
        'bleachbit'
    ]
    patterns = [f".*{keyword}.*" for keyword in SUSPICIOUS_KEYWORDS]
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)

# XML 파일을 파싱하여 의심스러운 항목을 CSV에 기록하는 함수
def parse_xml_and_write_suspicious_to_csv(xml_file_path, csv_file_path, username):
    try:
        tree = ET.parse(xml_file_path)
        root = tree.getroot()

        with open(csv_file_path, mode='w', newline='', encoding='utf-8') as file:
            csv_writer = csv.writer(file)
            # CSV 헤더 작성
            csv_writer.writerow([
                'Item Name',
                'Creation Time',
                'Access Time',
                'Write Time',
                'Target Path',
                'USB Name'
            ])

            # XML 파일에서 각 LnkFile 요소 반복 처리
            for lnk_file in root.findall('LnkFile'):
                file_path = lnk_file.find('file_path').text
                target_file_path = lnk_file.find('target_file_path').text
                creation_time = lnk_file.find('creation_time').text
                access_time = lnk_file.find('access_time').text
                write_time = lnk_file.find('write_time').text
                usb_name = lnk_file.find('usb_name').text

                # 사용자 경로 업데이트
                updated_file_path = update_user_path(file_path, username)
                updated_target_path = update_user_path(target_file_path, username)

                # 의심스러운 항목 감지
                combined_text = f"{updated_file_path} {updated_target_path}"
                if is_suspicious(combined_text):
                    print(f"의심스러운 항목 감지: {updated_file_path}, Target: {updated_target_path}")

                    # CSV에 의심스러운 항목 기록
                    csv_writer.writerow([
                        os.path.basename(updated_file_path),
                        creation_time,
                        access_time,
                        write_time,
                        updated_target_path,
                        usb_name
                    ])

        print(f"의심스러운 항목이 {csv_file_path}에 저장되었습니다.")

    except Exception as e:
        print(f"XML 처리 중 오류 발생: {e}")

# 외부 스크립트 경로 설정
script_path = r"..\\web\\find_user_for_externel.py"  # Raw string 또는 두 번의 백슬래시 사용

# 외부 스크립트를 통해 사용자 이름 목록 가져오기
usernames = get_usernames_from_script(script_path)

# 여러 사용자를 반복적으로 처리
for username in usernames:
    # XML 파일 및 CSV 파일 경로 설정 (raw string 사용)
    xml_file_path = fr'..\..\output\artifact\LNK\lnk_files_{username}.xml'  # 사용자에 맞는 XML 경로
    csv_file_path = fr'..\..\output\suspicious_artifact\\LNK\suspicious_antiforensic_lnk_files_{username}.csv'  # 사용자에 맞는 CSV 경로

    # XML 파일을 파싱하여 CSV로 저장
    parse_xml_and_write_suspicious_to_csv(xml_file_path, csv_file_path, username)
