import os
import win32com.client
import datetime
import pythoncom
import csv
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
import win32api  # 추가
import subprocess

# 외부 스크립트에서 사용자 정보 가져오기
def get_users_from_external_script(script_path):
    """외부 스크립트 실행 후 유효한 사용자 정보만 가져오기"""
    try:
        command = ['python', script_path]
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        users_data = {}
        print("외부 스크립트 실행 결과:")
        print(result.stdout)  # 스크립트의 출력 결과 출력

        # 결과를 기반으로 사용자 데이터 파싱
        for line in result.stdout.splitlines():
            # 유효한 사용자 이름을 포함하는 줄만 처리 (숫자 및 알파벳, 한글 등으로 구성된 경우만)
            if ":" in line and "Found valid username" not in line:
                try:
                    username, rest = line.split(":", 1)
                    username = username.strip()
                    # username에 실제 값이 있고 "Unknown"이 아닌 경우만 저장
                    if username and "Unknown" not in username and "RID" not in username:
                        users_data[username] = rest.strip()  # 유효한 Username: RID 저장
                except ValueError:
                    continue  # 잘못된 형식 무시
        return users_data
    except subprocess.CalledProcessError as e:
        print(f"외부 스크립트를 실행하는 중 오류 발생: {e}")
        return {}

def parse_lnk_file(file_path, shell):
    try:
        shortcut = shell.CreateShortCut(file_path)
        target_path = shortcut.Targetpath

        # 파일 시간 정보 가져오기
        creation_time = datetime.datetime.fromtimestamp(os.path.getctime(file_path))
        access_time = datetime.datetime.fromtimestamp(os.path.getatime(file_path))
        write_time = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))

        # USB 또는 이동식 디스크 확인
        usb_name = None
        if target_path and (target_path.startswith(r"\\") or (len(target_path) > 1 and target_path[1] == ":")):
            drive_letter = target_path[0:2]
            if drive_letter.upper() != "C:":  # C 드라이브가 아닌 경우
                try:
                    # 볼륨 레이블 가져오기
                    volume_info = win32api.GetVolumeInformation(drive_letter + '\\')
                    usb_name = volume_info[0]  # 볼륨 레이블
                except:
                    pass

        return {
            "file_path": file_path,
            "target_file_path": target_path if target_path else None,
            "creation_time": creation_time,
            "access_time": access_time,
            "write_time": write_time,
            "usb_name": usb_name
        }
    except Exception as e:
        print(f"Error parsing {file_path}: {str(e)}")
        return None

def analyze_lnk_files(directory):
    pythoncom.CoInitialize()  # COM 라이브러리 초기화
    lnk_data_list = []
    try:
        shell = win32com.client.Dispatch("WScript.Shell")
        for root, _, files in os.walk(directory):
            for file in files:
                if file.lower().endswith('.lnk'):
                    file_path = os.path.join(root, file)
                    lnk_info = parse_lnk_file(file_path, shell)
                    if lnk_info:
                        lnk_data_list.append(lnk_info)
    finally:
        pythoncom.CoUninitialize()  # COM 라이브러리 해제
    return lnk_data_list

def write_to_csv(data_list, csv_file):
    fieldnames = ["file_path", "target_file_path", "creation_time", "access_time", "write_time", "usb_name"]
    with open(csv_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for data in data_list:
            writer.writerow({
                "file_path": data['file_path'],
                "target_file_path": data['target_file_path'],
                "creation_time": data['creation_time'],
                "access_time": data['access_time'],
                "write_time": data['write_time'],
                "usb_name": data['usb_name']
            })

def write_to_xml(data_list, xml_file):
    root = ET.Element('LnkFiles')
    for data in data_list:
        lnk_elem = ET.SubElement(root, 'LnkFile')
        for key, value in data.items():
            child = ET.SubElement(lnk_elem, key)
            child.text = str(value)
    # 문자열로 변환하여 들여쓰기 적용
    xml_str = ET.tostring(root, encoding='utf-8')
    parsed_xml = minidom.parseString(xml_str)
    pretty_xml_str = parsed_xml.toprettyxml(indent="    ")
    with open(xml_file, 'w', encoding='utf-8') as f:
        f.write(pretty_xml_str)

if __name__ == "__main__":
    
    script_path = r"..\web\find_user_for_externel.py"  # 외부 스크립트 경로
    users_data = get_users_from_external_script(script_path)
    
    for user in users_data:  # 여러 사용자가 있을 수 있으므로 반복 처리
        # 사용자별 LNK 디렉토리 경로 설정
        lnk_directory = os.path.expandvars(f'..\\..\\output\\artifact\\LNK\\{user}_lnk')
        
        # LNK 파일 분석
        lnk_data_list = analyze_lnk_files(lnk_directory)

        # CSV로 저장
        csv_file = f'..\\..\\output\\artifact\\LNK\\lnk_files_{user}.csv'
        write_to_csv(lnk_data_list, csv_file)

        # XML로 저장
        xml_file = f'..\\..\\output\\artifact\\LNK\\lnk_files_{user}.xml'
        write_to_xml(lnk_data_list, xml_file)

        print(f"데이터가 {csv_file}와 {xml_file} 파일로 저장되었습니다.")
