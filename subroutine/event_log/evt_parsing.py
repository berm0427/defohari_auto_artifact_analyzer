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
def get_inode_number(image_path, offset, file_name, inode=None):
    """fls 도구로 파일 또는 디렉토리의 inode 번호를 가져오는 함수"""
    try:
        command = ['fls', '-f', 'ntfs', '-o', str(offset), image_path] if not inode else ['fls', '-f', 'ntfs', '-o', str(offset), image_path, inode]
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        
        for line in result.stdout.splitlines():
            if file_name in line:
                inode_number = line.split()[1].split(':')[0]
                return inode_number
    except subprocess.CalledProcessError as e:
        print(f"inode 번호를 찾는 중 오류 발생: {e}")
    return None

# 특정 사용자에 대해 Recent 폴더에서 lnk 파일을 추출하는 함수
def extract_evt_files(image_path, offset, output_dir):
    """ .evtx 파일(응용, 시스템, 보안)을 찾아서 추출"""

    # Windows 디렉토리 inode 가져오기
    windows_inode = get_inode_number(image_path, offset, "Windows")
    
    if windows_inode is None:
        print("Windows 디렉토리를 찾을 수 없습니다.")
        return
    print(f"Windows의 inode 번호: {windows_inode}")

    # System32 디렉토리 inode 가져오기
    System32_inode = get_inode_number(image_path, offset, "System32", windows_inode)
    
    if System32_inode is None:
        print("System32 디렉토리를 찾을 수 없습니다.")
        return
    print(f"System32의 inode 번호: {System32_inode}")

    # 'winevt' 디렉토리 inode 가져오기
    winevt_inode = get_inode_number(image_path, offset, "winevt", System32_inode)
    
    if not winevt_inode:
        print("'winevt' 디렉토리를 찾을 수 없습니다.")
        return
    print(f"winevt의 inode 번호: {winevt_inode}")

    # 'Logs' 디렉토리 inode 가져오기
    Logs_inode = get_inode_number(image_path, offset, "Logs", winevt_inode)
    
    if not Logs_inode:
        print("'Logs' 디렉토리를 찾을 수 없습니다.")
        return
    print(f"Logs의 inode 번호: {Logs_inode}")

    # 'Logs' 디렉토리에서 .evtx 파일 추출
    evtx_files = subprocess.run(['fls', '-f', 'ntfs', '-o', str(offset), image_path, Logs_inode], capture_output=True, text=True, check=True).stdout.splitlines()
    
    name_list = {'Application', 'Security', 'System'}
    
    for line in evtx_files:
        if ".evtx" in line.lower():  # 확장자는 이미 별도로 검사
            parts = line.split()
            evtx_inode = parts[1].split(":")[0]
            evtx_filename = " ".join(parts[2:])  # 공백을 포함한 전체 파일명 추출

            evtx_output_path = os.path.join(output_dir, evtx_filename)
            
            base_filename = evtx_filename.split('.')[0]  # 확장자를 제외한 파일명 추출
            
            if base_filename in name_list:  # 확장자를 제외한 파일명만 비교
                try:
                    # icat을 사용하여 inode 번호로 파일을 추출
                    command = ['icat', '-f', 'ntfs', '-o', str(offset), image_path, evtx_inode]
                    with open(evtx_output_path, 'wb') as f:
                        subprocess.run(command, stdout=f, check=True)
                    print(f"{evtx_output_path}에 {evtx_inode}를 가진 {evtx_filename} 파일 추출 성공")
                except subprocess.CalledProcessError as e:
                    print(f"evtx 파일 추출 중 오류 발생: {e}")
                    
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
    output_dir = r"..\..\output\artifact\event_log"  # 추출할 디렉토리 경로

    #image_path = r"..\..\image_here\file_extract.E01"
    
    # 파티션 오프셋 가져오기
    partition_offset = get_partition_offset(first_disk_image_path)
    
    if partition_offset:
        extract_evt_files(first_disk_image_path, partition_offset, output_dir)
