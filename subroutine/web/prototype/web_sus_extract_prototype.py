import subprocess
import shutil
import os
import re

# 안티 포렌식 관련 의심 키워드 목록
anti_forensic_keywords = [
    r'(?i).*ccleaner.*', r'(?i).*cleaner.*', r'(?i).*eraser.*',
    r'(?i).*wiper.*', r'(?i).*scrubber.*', r'(?i).*delete.*',
    r'(?i).*remove.*', r'(?i).*destroy.*', r'(?i).*bleachbit.*'
]

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

def get_partition_offset(image_path):
    """mmls 도구로 Basic data partition의 오프셋을 가져오는 함수"""
    command = ['mmls', image_path]
    result = run_command(command)
    for line in result.splitlines():
        if "NTFS" in line or "Basic data partition" in line:
            parts = line.split()
            offset = parts[2]
            print(f"파티션 오프셋 찾음: {offset}")
            return int(offset)
    return None

def get_inode_number(image_path, offset, file_name, inode=None):
    """fls 도구로 파일 또는 디렉토리의 inode 번호를 가져오는 함수"""
    command = ['fls', '-f', 'ntfs', '-o', str(offset), image_path] if not inode else ['fls', '-f', 'ntfs', '-o', str(offset), image_path, inode]
    result = run_command(command)
    for line in result.splitlines():
        if file_name in line and 'd/' in line:
            parts = line.split()
            inode_number = parts[1].split('-')[0]  # inode 번호는 "12345-144-1"에서 첫 번째 부분인 12345
            print(f"{file_name}의 inode 번호: {inode_number}")
            return inode_number
    return None

def search_suspicious_files(image_path, offset, downloads_inode):
    """Downloads 폴더에서 의심스러운 파일 검색"""
    suspicious_files = []
    command = ['fls', '-f', 'ntfs', '-o', str(offset), image_path, downloads_inode]
    result = run_command(command)

    for line in result.splitlines():
        if line.startswith('r/'):  # 파일인 경우
            file_name = ' '.join(line.split()[1:])
            if file_name.endswith(('.exe', '.msi', '.bat', '.cmd')) and any(re.search(keyword, file_name) for keyword in anti_forensic_keywords):
                suspicious_files.append(file_name)
                print(f"의심스러운 파일 발견: {file_name}")
    return suspicious_files

def extract_files(image_path, offset, suspicious_files, downloads_inode, destination_dir):
    """의심스러운 파일을 추출하여 destination_dir로 복사"""
    if not os.path.exists(destination_dir):
        os.makedirs(destination_dir)

    for file in suspicious_files:
        inode = file.split('-')[0]  # 파일의 inode 번호 추출
        command = ['icat', '-f', 'ntfs', '-o', str(offset), image_path, inode]
        file_data = run_command(command, binary_mode=True)  # 바이너리 모드로 데이터 처리

        # 파일 저장
        destination_path = os.path.join(destination_dir, os.path.basename(file))
        with open(destination_path, 'wb') as f:  # 바이너리 모드로 파일 쓰기
            f.write(file_data)
        print(f"파일 추출 완료: {destination_path}")

def get_users_from_registry():
    """subprocess를 사용해 web_find_user.py 실행 후 사용자 이름만 추출"""
    command = ['python', 'web_find_user.py']  # 업로드된 스크립트 실행
    result = run_command(command)

    users = []
    for line in result.splitlines():
        # 'Never logged in' 또는 타임스탬프가 있는 줄에서 사용자 이름 추출
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
    image_path = r"F:\file_extract_torrent.E01"  # 이미지 파일 경로
    output_dir = r"..\..\output\suspicious_file\web"  # 출력 디렉토리
    main(image_path, output_dir)
