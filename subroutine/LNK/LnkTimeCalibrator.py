import os
import subprocess
import datetime
import csv
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
import re
import logging
from dateutil import parser as date_parser  # dateutil 추가

# 로그 설정
logging.basicConfig(
    filename='lnk_time_extraction.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 시간 문자열을 파싱하는 헬퍼 함수
def parse_time(time_str):
    """소수점 이하 초가 있거나 없는 시간 문자열을 파싱"""
    try:
        return date_parser.parse(time_str)
    except ValueError as e:
        logging.error(f"시간 문자열 파싱 실패: {time_str} | 오류: {e}")
        return None

# 파티션 오프셋을 가져오는 함수
def get_partition_offset(image_path, partition_type="Basic data partition"):
    """mmls 도구로 특정 파티션의 오프셋을 가져오는 함수"""
    try:
        command = ['mmls', image_path]
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        
        lines = result.stdout.splitlines()
        for line in lines:
            if partition_type.lower() in line.lower():
                parts = line.split()
                if len(parts) > 2:
                    offset = parts[2]
                    print(f"파티션 오프셋 찾음: {offset}")
                    logging.info(f"파티션 오프셋 찾음: {offset}")
                    return int(offset)
        logging.error(f"지정된 파티션 타입 '{partition_type}'을 찾을 수 없습니다.")
    except subprocess.CalledProcessError as e:
        print(f"파티션 오프셋을 찾는 중 오류 발생: {e}")
        logging.error(f"파티션 오프셋을 찾는 중 오류 발생: {e}")
    return None

# 디스크 이미지 파일 찾기
def get_first_disk_image_path(image_directory):
    """지정된 디렉토리에서 첫 번째 디스크 이미지 파일(.e01)을 찾는 함수"""
    disk_image_extensions = ['.e01']

    try:
        for filename in os.listdir(image_directory):
            if any(filename.lower().endswith(ext) for ext in disk_image_extensions):
                image_path = os.path.join(image_directory, filename)
                print(f"디스크 이미지 파일 찾음: {image_path}")
                logging.info(f"디스크 이미지 파일 찾음: {image_path}")
                return image_path
        logging.error(f"지정된 디렉토리 '{image_directory}'에서 이미지 파일을 찾을 수 없습니다.")
    except Exception as e:
        logging.error(f"디스크 이미지 파일을 찾는 중 오류 발생: {e}")
    
    return None

# 특정 디렉토리의 inode를 찾는 함수
def get_directory_inode(image_path, offset, parent_inode, target_directory):
    """특정 inode 아래에서 디렉토리 inode를 검색"""
    try:
        # fls -D 옵션은 디렉토리 inode를 나열
        command = ['fls', '-D', '-f', 'ntfs', '-o', str(offset), image_path, str(parent_inode)]
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        
        # 각 줄은 'd/d inode_number: directory-name'
        pattern = re.compile(r'^d/d\s+(\d+-\d+-\d+):\s+' + re.escape(target_directory) + r'$', re.IGNORECASE)
        
        for line in result.stdout.splitlines():
            logging.debug(f"fls output line: {line}")  # 각 라인 로그 기록
            match = pattern.match(line)
            if match:
                inode_number = match.group(1)
                print(f"{target_directory}의 inode 번호: {inode_number}")
                logging.info(f"{target_directory}의 inode 번호: {inode_number}")
                return inode_number
        logging.error(f"{target_directory} 디렉토리를 찾을 수 없습니다.")
    except subprocess.CalledProcessError as e:
        print(f"디렉토리 inode를 찾는 중 오류 발생: {e}")
        logging.error(f"디렉토리 inode를 찾는 중 오류 발생: {e}")
    return None

# 중첩된 디렉토리 경로를 탐색하여 최종 디렉토리의 inode를 가져오는 함수
def get_nested_directory_inode(image_path, offset, parent_inode, path_list):
    """
    주어진 경로 리스트를 따라 중첩된 디렉토리의 inode를 반환합니다.
    path_list는 ['AppData', 'Roaming', 'Microsoft', 'Windows', 'Recent']와 같은 리스트입니다.
    """
    current_inode = parent_inode
    for directory in path_list:
        inode = get_directory_inode(image_path, offset, current_inode, directory)
        if not inode:
            logging.error(f"디렉토리 '{directory}'를 찾을 수 없습니다.")
            return None
        current_inode = inode
    return current_inode

# .lnk 파일 목록을 가져오는 함수
def get_lnk_files(image_path, offset, start_inode=None):
    """fls 도구를 사용하여 모든 .lnk 파일의 inode 번호와 경로를 가져오는 함수 (재귀적으로 검색)"""
    try:
        command = ['fls', '-f', 'ntfs', '-o', str(offset), '-r', image_path]
        if start_inode:
            command.append(str(start_inode))
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        lnk_files = []

        # fls 명령어 전체 출력 로그 기록
        logging.debug(f"fls 명령어 전체 출력:\n{result.stdout}")

        # Regex 패턴을 사용하여 .lnk 파일의 inode와 경로를 정확하게 추출
        # 수정된 패턴: 모든 접두사를 포괄
        pattern = compile(r'^[^:]*\s+(\d+-\d+-\d+):\s+(.*\.lnk)$', re.IGNORECASE)
        
        for line in result.stdout.splitlines():
            match = pattern.match(line)
            if match:
                inode = match.group(1)
                file_path = match.group(2).replace('/', '\\')
                lnk_files.append({'inode': inode, 'file_path': file_path})
                logging.debug(f"찾은 .lnk 파일: {file_path}, inode: {inode}")
                print(f"찾은 .lnk 파일: {file_path}, inode: {inode}")  # 실시간 출력
        logging.info(f"찾은 .lnk 파일 수: {len(lnk_files)}")
        return lnk_files
    except subprocess.CalledProcessError as e:
        logging.error(f"fls를 실행하는 중 오류 발생: {e}")
        print(f"fls를 실행하는 중 오류 발생: {e}")
        return []
    except Exception as e:
        logging.error(f".lnk 파일 목록을 가져오는 중 오류 발생: {e}")
        print(f".lnk 파일 목록을 가져오는 중 오류 발생: {e}")
        return []

# istat를 사용하여 파일의 원본 시간 정보 추출
def get_file_times(image_path, offset, inode_number):
    """istat 도구를 사용하여 파일의 원본 생성, 접근, 수정 시간을 가져오는 함수"""
    try:
        command = ['istat', '-f', 'ntfs', '-o', str(offset), image_path, str(inode_number)]
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        creation_time = access_time = write_time = None

        # istat 출력 전체를 로그에 기록
        logging.debug(f"istat 명령어 출력 ({inode_number}):\n{result.stdout}")

        # Created, File Modified, Accessed 정보를 추출하기 위한 정규 표현식 패턴
        created_pattern = r'Created:\s+(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:\.\d+)?)'
        mtime_pattern = r'File Modified:\s+(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:\.\d+)?)'
        atime_pattern = r'Accessed:\s+(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:\.\d+)?)'

        # Created 추출
        created_match = re.search(created_pattern, result.stdout)
        if created_match:
            created_str = created_match.group(1)
            creation_time = parse_time(created_str)
            if creation_time:
                logging.debug(f"Parsed Created: {creation_time}")
        else:
            logging.error(f"Created 정보를 찾을 수 없습니다: inode {inode_number}")

        # File Modified (Mtime) 추출
        mtime_match = re.search(mtime_pattern, result.stdout)
        if mtime_match:
            mtime_str = mtime_match.group(1)
            write_time = parse_time(mtime_str)
            if write_time:
                logging.debug(f"Parsed Mtime: {write_time}")
        else:
            logging.error(f"Mtime 정보를 찾을 수 없습니다: inode {inode_number}")

        # Accessed (Atime) 추출
        atime_match = re.search(atime_pattern, result.stdout)
        if atime_match:
            atime_str = atime_match.group(1)
            access_time = parse_time(atime_str)
            if access_time:
                logging.debug(f"Parsed Atime: {access_time}")
        else:
            logging.error(f"Atime 정보를 찾을 수 없습니다: inode {inode_number}")

        return creation_time, access_time, write_time
    except subprocess.CalledProcessError as e:
        logging.error(f"istat를 실행하는 중 오류 발생: {e}")
        return None, None, None
    except Exception as e:
        logging.error(f"시간 정보를 파싱하는 중 오류 발생: {e}")
        return None, None, None

# CSV로 저장하는 함수
def write_to_csv(data_list, csv_file):
    fieldnames = ["file_path", "creation_time", "access_time", "write_time"]
    try:
        with open(csv_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for data in data_list:
                writer.writerow({
                    "file_path": data['file_path'],
                    "creation_time": data['creation_time'].strftime('%Y-%m-%d %H:%M:%S') if data['creation_time'] else 'N/A',
                    "access_time": data['access_time'].strftime('%Y-%m-%d %H:%M:%S') if data['access_time'] else 'N/A',
                    "write_time": data['write_time'].strftime('%Y-%m-%d %H:%M:%S') if data['write_time'] else 'N/A',
                })
        logging.info(f"CSV 파일 작성 완료: {csv_file}")
        print(f"CSV 파일 작성 완료: {csv_file}")
    except Exception as e:
        logging.error(f"CSV 파일 작성 중 오류 발생: {e}")
        print(f"CSV 파일 작성 중 오류 발생: {e}")

# XML로 저장하는 함수
def write_to_xml(data_list, xml_file):
    try:
        root = ET.Element('LnkFiles')
        for data in data_list:
            lnk_elem = ET.SubElement(root, 'LnkFile')
            for key, value in data.items():
                child = ET.SubElement(lnk_elem, key)
                if isinstance(value, datetime.datetime):
                    child.text = value.strftime('%Y-%m-%d %H:%M:%S')
                elif value is None:
                    child.text = 'N/A'
                else:
                    child.text = str(value)
        # 문자열로 변환하여 들여쓰기 적용
        xml_str = ET.tostring(root, encoding='utf-8')
        parsed_xml = minidom.parseString(xml_str)
        pretty_xml_str = parsed_xml.toprettyxml(indent="    ")
        with open(xml_file, 'w', encoding='utf-8') as f:
            f.write(pretty_xml_str)
        logging.info(f"XML 파일 작성 완료: {xml_file}")
        print(f"XML 파일 작성 완료: {xml_file}")
    except Exception as e:
        logging.error(f"XML 파일 작성 중 오류 발생: {e}")
        print(f"XML 파일 작성 중 오류 발생: {e}")

# 모든 파일을 나열하여 디버깅하기 위한 함수
def get_all_files(image_path, offset, start_inode=None):
    """fls 도구를 사용하여 모든 파일의 inode 번호와 경로를 가져오는 함수 (재귀적으로 검색)"""
    try:
        command = ['fls', '-f', 'ntfs', '-o', str(offset), '-r', image_path]
        if start_inode:
            command.append(str(start_inode))
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        all_files = []

        # fls 명령어 전체 출력 로그 기록
        logging.debug(f"fls 명령어 전체 출력:\n{result.stdout}")

        # 모든 파일을 캡처하는 정규 표현식 패턴
        # 예시 fls 출력:
        # r/r 112590-128-1: forensics.lnk
        pattern = re.compile(r'^[^:]*\s+(\d+-\d+-\d+):\s+(.*)$', re.IGNORECASE)

        for line in result.stdout.splitlines():
            match = pattern.match(line)
            if match:
                inode = match.group(1)
                file_path = match.group(2).replace('/', '\\')
                all_files.append({'inode': inode, 'file_path': file_path})
                logging.debug(f"찾은 파일: {file_path}, inode: {inode}")
                print(f"찾은 파일: {file_path}, inode: {inode}")  # 실시간 출력
        logging.info(f"찾은 파일 수: {len(all_files)}")
        return all_files
    except subprocess.CalledProcessError as e:
        logging.error(f"fls를 실행하는 중 오류 발생: {e}")
        print(f"fls를 실행하는 중 오류 발생: {e}")
        return []
    except Exception as e:
        logging.error(f"파일 목록을 가져오는 중 오류 발생: {e}")
        print(f"파일 목록을 가져오는 중 오류 발생: {e}")
        return []

def main():
    # 기본 경로 설정 (스크립트의 현재 위치를 기준으로 상대 경로 설정)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_image_dir = os.path.normpath(os.path.join(script_dir, "../../image_here"))
    default_output_dir = os.path.normpath(os.path.join(script_dir, "../../output/artifact/LNK"))

    print("===== LNK 아티팩트 시간 정보 추출 시작 =====")
    logging.info("===== LNK 아티팩트 시간 정보 추출 시작 =====")

    # 디스크 이미지 파일 찾기
    first_disk_image_path = get_first_disk_image_path(default_image_dir)

    if not first_disk_image_path:
        logging.error("디스크 이미지 파일을 찾을 수 없습니다.")
        print("디스크 이미지 파일을 찾을 수 없습니다.")
        exit(1)

    output_dir = default_output_dir  # 추출할 디렉토리 경로
    os.makedirs(output_dir, exist_ok=True)

    # 파티션 오프셋 가져오기
    partition_offset = get_partition_offset(first_disk_image_path, "Basic data partition")

    if partition_offset is None:
        logging.error("파티션 오프셋을 찾을 수 없습니다.")
        print("파티션 오프셋을 찾을 수 없습니다.")
        exit(1)

    # 'Users' 디렉토리의 inode 번호 가져오기 (NTFS의 루트 inode는 5)
    users_inode = get_directory_inode(first_disk_image_path, partition_offset, 5, 'Users')

    if not users_inode:
        logging.error("'Users' 디렉토리를 찾을 수 없습니다.")
        print("'Users' 디렉토리를 찾을 수 없습니다.")
        exit(1)

    # 'Users' 디렉토리 내의 모든 사용자 폴더 검색
    try:
        command = ['fls', '-f', 'ntfs', '-o', str(partition_offset), first_disk_image_path, users_inode]
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        user_dirs = []
        pattern = re.compile(r'^d/d\s+(\d+-\d+-\d+):\s+(.*)$', re.IGNORECASE)

        for line in result.stdout.splitlines():
            match = pattern.match(line)
            if match:
                inode = match.group(1)
                username = match.group(2)
                user_dirs.append({'inode': inode, 'username': username})
                logging.debug(f"찾은 사용자 디렉토리: {username}, inode: {inode}")
                print(f"찾은 사용자 디렉토리: {username}, inode: {inode}")

        logging.info(f"찾은 사용자 수: {len(user_dirs)}")
    except subprocess.CalledProcessError as e:
        logging.error(f"'Users' 디렉토리 내 사용자 목록을 가져오는 중 오류 발생: {e}")
        print(f"'Users' 디렉토리 내 사용자 목록을 가져오는 중 오류 발생: {e}")
        user_dirs = []

    if not user_dirs:
        logging.warning("'Users' 디렉토리 내에 사용자 폴더가 존재하지 않습니다.")
        print("'Users' 디렉토리 내에 사용자 폴더가 존재하지 않습니다.")
        exit(0)

    # 사용자별로 데이터 분리
    for user in user_dirs:
        username = user['username']
        user_inode = user['inode']
        recent_path = ["AppData", "Roaming", "Microsoft", "Windows", "Recent"]
        logging.info(f"{username} 사용자에 대한 'Recent' 디렉토리 검색 시작")
        print(f"{username} 사용자에 대한 'Recent' 디렉토리 검색 시작")

        # 'Recent' 디렉토리의 inode 번호 가져오기 (중첩된 경로 탐색)
        recent_inode = get_nested_directory_inode(first_disk_image_path, partition_offset, user_inode, recent_path)

        if not recent_inode:
            logging.warning(f"{username} 사용자의 'Recent' 디렉토리를 찾을 수 없습니다.")
            print(f"{username} 사용자의 'Recent' 디렉토리를 찾을 수 없습니다.")
            continue

        # 'Recent' 디렉토리 내의 모든 파일 목록 가져오기
        all_files = get_all_files(first_disk_image_path, partition_offset, start_inode=recent_inode)

        if not all_files:
            logging.info(f"{username} 사용자의 'Recent' 디렉토리에 파일이 존재하지 않습니다.")
            print(f"{username} 사용자의 'Recent' 디렉토리에 파일이 존재하지 않습니다.")
            continue

        # .lnk 파일만 필터링
        lnk_files = [file for file in all_files if file['file_path'].lower().endswith('.lnk')]

        logging.info(f"찾은 .lnk 파일 수: {len(lnk_files)}")
        if not lnk_files:
            logging.info(f"{username} 사용자의 'Recent' 디렉토리에 .lnk 파일이 존재하지 않습니다.")
            print(f"{username} 사용자의 'Recent' 디렉토리에 .lnk 파일이 존재하지 않습니다.")
            continue

        # 사용자별 extracted_data 초기화
        user_extracted_data = []

        # 각 .lnk 파일의 MAC 타임 정보 추출
        for lnk in lnk_files:
            inode = lnk['inode']
            file_path = lnk['file_path']
            creation_time, access_time, write_time = get_file_times(first_disk_image_path, partition_offset, inode)
            user_extracted_data.append({
                "file_path": file_path,
                "creation_time": creation_time,
                "access_time": access_time,
                "write_time": write_time
            })
            logging.info(f"{file_path}의 시간 정보 추출 완료")
            print(f"{file_path}의 시간 정보 추출 완료")

        # 사용자별 데이터 저장
        if user_extracted_data:
            csv_file = os.path.join(output_dir, f'lnk_files_time_{username}.csv')
            xml_file = os.path.join(output_dir, f'lnk_files_time_{username}.xml')

            write_to_csv(user_extracted_data, csv_file)
            write_to_xml(user_extracted_data, xml_file)

    print("===== LNK 아티팩트 시간 정보 추출 종료 =====")
    logging.info("===== LNK 아티팩트 시간 정보 추출 종료 =====")

if __name__ == "__main__":
    main()
