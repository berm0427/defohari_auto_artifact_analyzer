import os
import subprocess
import re

anti_forensic_keywords = [
    r'(?i).*ccleaner.*', r'(?i).*cleaner.*', r'(?i).*eraser.*',
    r'(?i).*wiper.*', r'(?i).*scrubber.*', r'(?i).*delete.*',
    r'(?i).*remove.*', r'(?i).*destroy.*', r'(?i).*bleachbit.*'
]

def get_first_disk_image_path(image_directory):
    # 디스크 이미지 파일 확장자 목록
    disk_image_extensions = ['.e01']
    
    # 지정된 디렉토리에서 모든 파일을 검색
    for filename in os.listdir(image_directory):
        # 파일 확장자를 소문자로 변환하여 확인
        if any(filename.lower().endswith(ext) for ext in disk_image_extensions):
            # 첫 번째 이미지 파일을 찾으면 그 경로 반환
            return os.path.join(image_directory, filename)

    # 이미지 파일이 없을 경우 None 반환
    return None



def run_command(command, binary_mode=False):
    """명령어 실행 및 결과 출력"""
    print(f"Running command: {' '.join(command)}")
    
    if binary_mode:
        # 바이너리 데이터를 처리하기 위한 모드
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.stderr:
            print(f"Command error: {result.stderr.strip().decode('utf-8')}")
        return result.stdout  # 바이너리 데이터를 반환
    else:
        # 일반적인 텍스트 처리
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.stderr:
            print(f"Command error: {result.stderr.strip()}")
        return result.stdout.strip()

def sanitize_file_name(file_name):
    """파일 이름에서 Windows에서 허용되지 않는 문자를 제거하고 공백, 탭을 정리"""
    cleaned_file_name = file_name.split(':')[-1].strip()  # inode 번호 앞의 부분을 제거
    sanitized_name = re.sub(r'[<>:"/\\|?*]', '_', cleaned_file_name)  # 허용되지 않는 문자 제거
    sanitized_name = sanitized_name.replace('\t', '').replace('\n', '').strip()  # 탭 및 개행 제거, 앞뒤 공백 제거
    return sanitized_name

def extract_files(image_path, offset, suspicious_files, downloads_inode, destination_dir):
    """의심스러운 파일을 추출하여 destination_dir로 복사"""
    if not os.path.exists(destination_dir):
        os.makedirs(destination_dir)

    for file_entry in suspicious_files:
        # 파일 이름 및 inode 번호 추출
        try:
            inode, file_name = file_entry.split(':', 1)
            inode = inode.strip()  # 정확한 inode 번호만 사용
            file_name = file_name.strip()  # 파일 이름 정리
        except Exception as e:
            print(f"파일 이름을 처리하는 중 오류 발생: {e}")
            continue

        # 파일 이름에서 비허용 문자 제거
        sanitized_file_name = sanitize_file_name(file_name)

        # icat 명령을 실행하여 파일 추출
        command = ['icat', '-f', 'ntfs', '-o', str(offset), image_path, inode]
        file_data = run_command(command, binary_mode=True)  # 바이너리 모드로 데이터 처리

        # icat 명령어로 추출한 파일의 크기 확인
        if not file_data or len(file_data) == 0:
            print(f"icat 명령으로 {sanitized_file_name}에서 데이터를 추출할 수 없었습니다. 데이터가 없습니다.")
            continue

        print(f"추출한 데이터 크기: {len(file_data)} 바이트")

        # 파일 저장 경로 설정 및 저장
        destination_path = os.path.join(destination_dir, sanitized_file_name)  # 실제 파일 이름 사용
        try:
            with open(destination_path, 'wb') as f:  # 바이너리 모드로 파일 쓰기
                f.write(file_data)
            print(f"파일 추출 완료: {destination_path}")
        except Exception as e:
            print(f"파일 저장 중 오류 발생: {e}")

def search_suspicious_files(image_path, offset, downloads_inode):
    """Downloads 폴더에서 의심스러운 파일 검색"""
    suspicious_files = []
    command = ['fls', '-f', 'ntfs', '-o', str(offset), image_path, downloads_inode]
    result = run_command(command)

    for line in result.splitlines():
        if line.startswith('r/'):  # 파일인 경우
            try:
                parts = line.split(None, 1)
                inode = parts[1].split('-')[0]  # inode 번호만 추출
                file_name = parts[1] if len(parts) > 1 else ''
                if file_name.endswith(('.exe', '.msi', '.bat', '.cmd')) and any(re.search(keyword, file_name) for keyword in anti_forensic_keywords):
                    suspicious_files.append(f"{inode}: {file_name}")
                    print(f"의심스러운 파일 발견: {file_name}")
            except Exception as e:
                print(f"파일 검색 중 오류 발생: {e}")
    return suspicious_files

def get_partition_offset(image_path):
    """mmls 도구로 Basic data partition의 오프셋을 가져오는 함수"""
    try:
        command = ['mmls', image_path]
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        lines = result.stdout.splitlines()
        for line in lines:
            if "Basic data partition" in line:
                parts = line.split()
                if len(parts) > 2:
                    offset = parts[2]
                    print(f"파티션 오프셋 찾음: {offset}")
                    return int(offset)
    except subprocess.CalledProcessError as e:
        print(f"파티션 오프셋을 찾는 중 오류 발생: {e}")
    return None

def get_inode_number(image_path, offset, file_name, inode=None):
    """fls 도구로 파일 또는 디렉토리의 inode 번호를 가져오는 함수"""
    try:
        # inode 값이 없다면 루트에서 검색, 있다면 해당 디렉토리 내에서 검색
        command = ['fls', '-f', 'ntfs', '-o', str(offset), image_path] if not inode else ['fls', '-f', 'ntfs', '-o', str(offset), image_path, inode]
        result = run_command(command)
        
        for line in result.splitlines():
            # 파일 이름이 디렉토리인지, 그리고 정확히 일치하는지 확인
            if file_name in line and line.startswith('d/d'):  # 디렉토리만 가져옴
                inode_info = line.split()[1].split('-')[0]  # inode 번호만 추출
                print(f"{file_name}의 inode 번호: {inode_info}")
                return inode_info
    except subprocess.CalledProcessError as e:
        print(f"inode 번호를 찾는 중 오류 발생: {e}")
    return None
    
def get_users_from_registry():
    """subprocess를 사용해 web_find_user.py 실행 후 사용자 이름만 추출"""
    command = ['python', 'web_find_user.py']  # 업로드된 스크립트 실행
    result = run_command(command)

    users = []
    for line in result.splitlines():
        if ':' in line and ('Never logged in' in line or re.search(r'\d{4}-\d{2}-\d{2}', line)):
            username = line.split(':')[0].strip()  # 사용자 이름 부분만 추출
            if '<Unknown>' not in username:  # <Unknown>은 제외
                users.append(username)
    print(f"사용자 목록: {users}")
    return users

def main(image_path, output_dir):
    # 파티션 오프셋 가져오기
    partition_offset = get_partition_offset(image_path)
    if not partition_offset:
        print("파티션 오프셋을 찾지 못했습니다.")
        return

    # 레지스트리 하이브에서 사용자 정보 가져오기
    users = get_users_from_registry()
    if not users:
        print("사용자 정보를 가져오지 못했습니다.")
        return

    for user in users:
        # Users 디렉토리에서 해당 사용자 디렉토리 inode 찾기
        users_inode = get_inode_number(image_path, partition_offset, 'Users')
        if not users_inode:
            print(f"Users 디렉토리를 찾지 못했습니다.")
            continue

        user_inode = get_inode_number(image_path, partition_offset, user, users_inode)
        if not user_inode:
            print(f"사용자 {user} 디렉토리를 찾지 못했습니다.")
            continue

        # Downloads 디렉토리 inode 찾기
        downloads_inode = get_inode_number(image_path, partition_offset, 'Downloads', user_inode)
        if not downloads_inode:
            print(f"사용자 {user}의 Downloads 디렉토리를 찾지 못했습니다.")
            continue

        # 의심스러운 파일 검색 및 추출
        suspicious_files = search_suspicious_files(image_path, partition_offset, downloads_inode)
        if suspicious_files:
            print(f"{user}의 의심스러운 파일: {len(suspicious_files)}개 발견")
            extract_files(image_path, partition_offset, suspicious_files, downloads_inode, os.path.join(output_dir, user))
        else:
            print(f"{user}의 의심스러운 파일을 찾지 못했습니다.")

if __name__ == "__main__":
    image_path_directory = r"..\..\image_here"
    image_path = get_first_disk_image_path(image_path_directory)  # 이미지 파일 경로
    output_dir = r"..\..\output\suspicious_file\web"  # 출력 디렉토리
    main(image_path, output_dir)
