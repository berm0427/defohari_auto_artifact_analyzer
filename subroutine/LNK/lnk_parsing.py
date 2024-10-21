import os
import subprocess

# 파티션 오프셋을 가져오는 함수
def get_partition_offset(image_path, partition_type="Basic data partition"):
    """mmls 도구로 Basic data partition의 오프셋을 가져오는 함수"""
    try:
        command = ['mmls', image_path]
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        
        lines = result.stdout.splitlines()
        for line in lines:
            if partition_type in line:
                parts = line.split()
                if len(parts) > 2:
                    offset = parts[2]
                    print(f"파티션 오프셋 찾음: {offset}")
                    return int(offset)
    except subprocess.CalledProcessError as e:
        print(f"파티션 오프셋을 찾는 중 오류 발생: {e}")
    return None

# inode 번호를 가져오는 함수
def get_inode_number(image_path, offset, dir_inode=None):
    """fls 도구로 파일 또는 디렉토리의 inode 번호를 가져오는 함수"""
    try:
        # fls 명령어 실행 (특정 디렉토리 inode가 없으면 루트 디렉토리에서 시작)
        command = ['fls', '-f', 'ntfs', '-o', str(offset), image_path] if not dir_inode else ['fls', '-f', 'ntfs', '-o', str(offset), image_path, str(dir_inode)]
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        
        return result.stdout.splitlines()
    except subprocess.CalledProcessError as e:
        print(f"inode 번호를 찾는 중 오류 발생: {e}")
        return None

# 디렉토리 inode 번호만 가져오는 함수
def get_directory_inode(image_path, offset, parent_inode, target_directory):
    """특정 inode 아래에서 디렉토리 inode를 검색"""
    command = ['fls', '-D', '-f', 'ntfs', '-o', str(offset), image_path, parent_inode]
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    
    for line in result.stdout.splitlines():
        if target_directory in line and inode_number != '*':
            inode_number = line.split()[1].split(':')[0]
            print(f"{target_directory}의 inode 번호: {inode_number}")
            return inode_number
    return None


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


# 특정 디렉토리 안에서 이름을 기반으로 inode를 찾아 반환하는 함수
def find_inode(lines, target_name):
    """fls 출력에서 target_name에 해당하는 inode 번호 반환"""
    for line in lines:
        if target_name.lower() in line.lower():
            parts = line.split()
            inode = parts[1].split(":")[0]
            return inode
    return None

# 특정 사용자에 대해 Recent 폴더에서 lnk 파일을 추출하는 함수
def extract_lnk_files(image_path, offset, output_dir, username):
    """사용자의 Recent 폴더에서 .lnk 파일을 찾아서 추출"""
    # 사용자별 폴더 생성
    user_output_dir = os.path.join(output_dir, f"{username}_lnk")
    os.makedirs(user_output_dir, exist_ok=True)
    
    # 'Users' 디렉토리 inode 가져오기
    root_inode = get_inode_number(image_path, offset)
    users_inode = find_inode(root_inode, "Users")
    
    if not users_inode:
        print(f"'Users' 디렉토리를 찾을 수 없습니다.")
        return
    
    # 'Users/[username]' 디렉토리 inode 가져오기
    user_inode = get_inode_number(image_path, offset, users_inode)
    user_inode = find_inode(user_inode, username)
    
    if not user_inode:
        print(f"{username} 디렉토리를 찾을 수 없습니다.")
        return

    # 'Users/[username]/AppData' 디렉토리 inode 가져오기
    appdata_inode = get_inode_number(image_path, offset, user_inode)
    appdata_inode = find_inode(appdata_inode, "AppData")
    
    if not appdata_inode:
        print(f"{username}의 'AppData' 디렉토리를 찾을 수 없습니다.")
        return

    # 'Users/[username]/AppData/Roaming' 디렉토리 inode 가져오기
    roaming_inode = get_inode_number(image_path, offset, appdata_inode)
    roaming_inode = find_inode(roaming_inode, "Roaming")
    
    if not roaming_inode:
        print(f"{username}의 'Roaming' 디렉토리를 찾을 수 없습니다.")
        return

    # 'Users/[username]/AppData/Roaming/Microsoft' 디렉토리 inode 가져오기
    microsoft_inode = get_inode_number(image_path, offset, roaming_inode)
    microsoft_inode = find_inode(microsoft_inode, "Microsoft")
    
    if not microsoft_inode:
        print(f"{username}의 'Microsoft' 디렉토리를 찾을 수 없습니다.")
        return

    # 'Users/[username]/AppData/Roaming/Microsoft/Windows' 디렉토리 inode 가져오기
    windows_inode = get_inode_number(image_path, offset, microsoft_inode)
    windows_inode = find_inode(windows_inode, "Windows")
    
    if not windows_inode:
        print(f"{username}의 'Windows' 디렉토리를 찾을 수 없습니다.")
        return

    # 'Users/[username]/AppData/Roaming/Microsoft/Windows/Recent' 디렉토리 inode 가져오기
    recent_inode = get_inode_number(image_path, offset, windows_inode)
    recent_inode = find_inode(recent_inode, "Recent")
    
    if not recent_inode:
        print(f"{username}의 'Recent' 디렉토리를 찾을 수 없습니다.")
        return

    # 'Recent' 디렉토리에서 .lnk 파일 추출
    recent_files = get_inode_number(image_path, offset, recent_inode)
    for line in recent_files:
        if ".lnk" in line.lower():
            try:
                parts = line.split()
                lnk_inode = parts[1].split(":")[0]
                if lnk_inode != '*':  # 유효한 inode인지 확인
                    lnk_filename = parts[-1]  # 파일명을 추출
                    lnk_output_path = os.path.join(user_output_dir, lnk_filename)
                    try:
                        # icat을 사용하여 inode 번호로 파일을 추출
                        command = ['icat', '-f', 'ntfs', '-o', str(offset), image_path, lnk_inode]
                        with open(lnk_output_path, 'wb') as f:
                            subprocess.run(command, stdout=f, check=True)
                        print(f"{lnk_output_path}에 .lnk 파일 추출 성공")
                    except subprocess.CalledProcessError as e:
                        print(f"lnk 파일 추출 중 오류 발생: {e}")
            except IndexError:
                print(f"라인을 파싱하는 중 오류 발생: {line}")

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
    
               
# 메인 실행 로직
if __name__ == "__main__":
    
    # 이미지 파일 경로 및 출력 디렉토리 설정
    image_path_directory = r"..\..\image_here"
    first_disk_image_path = get_first_disk_image_path(image_path_directory)

    #image_path = r"..\..\image_here\file_extract.E01"
    
    script_path = r"..\web\find_user_for_externel.py"  # 외부 스크립트 경로
    output_dir = r"..\..\output\artifact\LNK"  # 추출할 디렉토리 경로

    # 파티션 오프셋 가져오기
    partition_offset = get_partition_offset(first_disk_image_path)
    
    if partition_offset:
        # 외부 스크립트로부터 사용자 목록 가져오기
        users_data = get_users_from_external_script(script_path)
        
        for username in users_data:
            # 각 사용자별로 .lnk 파일을 추출
            extract_lnk_files(first_disk_image_path, partition_offset, output_dir, username)

