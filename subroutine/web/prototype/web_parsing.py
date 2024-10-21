import subprocess
import os

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
def get_inode_number(image_path, offset, file_name, inode=None):
    """fls 도구로 파일 또는 디렉토리의 inode 번호를 가져오는 함수"""
    try:
        command = ['fls', '-f', 'ntfs', '-o', str(offset), image_path] if not inode else ['fls', '-f', 'ntfs', '-o', str(offset), image_path, inode]
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        
        found_inodes = []
        for line in result.stdout.splitlines():
            if file_name in line:
                inode_number = line.split()[1].split(':')[0]
                found_inodes.append(inode_number)
                print(f"{file_name}의 inode 번호: {inode_number}")
        return found_inodes if found_inodes else None
    except subprocess.CalledProcessError as e:
        print(f"inode 번호를 찾는 중 오류 발생: {e}")
    return None

# 디렉토리 inode 번호만 가져오는 함수
def get_directory_inode(image_path, offset, parent_inode, target_directory):
    """특정 inode 아래에서 디렉토리 inode를 검색"""
    command = ['fls', '-f', 'ntfs', '-o', str(offset), image_path, parent_inode]
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    
    for line in result.stdout.splitlines():
        if target_directory in line:
            inode_number = line.split()[1].split(':')[0]
            print(f"{target_directory}의 inode 번호: {inode_number}")
            return inode_number
    return None

# 외부 스크립트에서 사용자 정보 가져오기
def get_users_from_external_script(script_path):
    """외부 스크립트 실행 후 사용자 정보 가져오기"""
    try:
        command = ['python', script_path]
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        users_data = {}
        print("외부 스크립트 실행 결과:")
        print(result.stdout)  # 스크립트의 출력 결과 출력

        # 결과를 기반으로 사용자 데이터 파싱
        for line in result.stdout.splitlines():
            if ":" in line:  # RID가 포함된 라인을 처리
                username, rest = line.split(":", 1)
                users_data[username.strip()] = rest.strip()  # Username: RID 저장
        return users_data
    except subprocess.CalledProcessError as e:
        print(f"외부 스크립트를 실행하는 중 오류 발생: {e}")
        return {}

# 파일을 추출하는 함수
def extract_file(image_path, offset, inode, output_dir, file_name):
    """icat 도구로 파일을 추출하는 함수"""
    try:
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, file_name)
        command = ['icat', '-f', 'ntfs', '-o', str(offset), image_path, inode]
        with open(output_file, 'wb') as f:
            result = subprocess.run(command, stdout=f, check=True)
        print(f"파일 추출 완료: {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"파일 추출 중 오류 발생: {e}")

def search_browser_history(image_path, partition_offset, output_dir):
    """각 사용자에 대해 브라우저 히스토리를 검색하고 추출하는 함수"""
    # Users 디렉토리 inode 가져오기
    users_inode = get_inode_number(image_path, partition_offset, "Users")
    
    if not users_inode:
        print("Users 디렉토리를 찾을 수 없습니다.")
        return

    users_data = get_users_from_external_script(script_path)

    if not users_data:
        print("사용자 정보를 찾을 수 없습니다.")
        return
    
    # 각 사용자에 대해 브라우저 히스토리를 탐색
    for username, rid in users_data.items():
        print(f"사용자 이름: {username}")
        
        # 사용자 홈 디렉토리 inode 가져오기
        user_inode = get_inode_number(image_path, partition_offset, username, users_inode[0])
        
        if not user_inode:
            print(f"사용자 {username}의 홈 디렉토리를 찾을 수 없습니다.")
            continue
        
        # 브라우저 관련 디렉토리 및 파일 탐색
        browser_directories = {
            "Edge": ("AppData", "Local", "Microsoft", "Edge", "User Data", "Default"),
            "Chrome": ("AppData", "Local", "Google", "Chrome", "User Data", "Default"),
            "Whale": ("AppData", "Local", "Naver", "Naver Whale", "User Data", "Default"),
            "Firefox": ("AppData", "Roaming", "Mozilla", "Firefox", "Profiles", ".default")
        }

        browser_history_file = {
            "Edge": "History",
            "Chrome": "History",
            "Whale": "History",
            "Firefox": "places.sqlite"
        }

        for browser, directories in browser_directories.items():
            current_inode = user_inode[0]  # Start from the user's home directory inode

            for directory in directories:
                current_inode = get_directory_inode(image_path, partition_offset, current_inode, directory)
                if not current_inode:
                    print(f"{browser} 브라우저의 '{directory}' 디렉토리를 찾을 수 없습니다.")
                    break
            else:
                # 브라우저의 히스토리 파일 탐색
                history_inode = get_inode_number(image_path, partition_offset, browser_history_file[browser], current_inode)
                if history_inode:
                    extract_file(image_path, partition_offset, history_inode[0], output_dir, browser_history_file[browser])

# 메인 실행 로직
if __name__ == "__main__":
    image_path = r"F:file_ext.raw"
    script_path = r"web_find_user.py"  # 외부 스크립트 경로
    output_dir = r"..\..\output\artifact\web"  # 추출할 디렉토리 경로

    # 파티션 오프셋 가져오기
    partition_offset = get_partition_offset(image_path)
    
    if partition_offset:
        search_browser_history(image_path, partition_offset, output_dir)
