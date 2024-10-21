import os
import subprocess

# mmls로 파티션 오프셋을 가져오는 함수
def get_partition_offset(image_path, partition_type="Basic data partition"):
    """mmls 도구로 Basic data partition의 오프셋을 가져오는 함수"""
    try:
        command = ['mmls', image_path]
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        
        # mmls 결과에서 각 줄을 배열로 처리하고, Basic data partition을 찾음
        lines = result.stdout.splitlines()
        for line in lines:
            if partition_type in line:
                parts = line.split()
                if len(parts) > 2:
                    offset = parts[2]  # Start 섹터 (세 번째 열)
                    print(f"파티션 오프셋 찾음: {offset}")
                    return int(offset)
    except subprocess.CalledProcessError as e:
        print(f"파티션 오프셋을 찾는 중 오류 발생: {e}")
    return None

# Sleuth Kit의 fls 도구로 inode 번호를 확인하는 함수
def get_inode_number(image_path, offset, file_name, inode=None):
    """fls 도구로 파일의 inode 번호를 가져오는 함수"""
    try:
        # inode가 주어지면 그 inode 내에서 검색, 그렇지 않으면 전체 파일 시스템에서 검색
        command = ['fls', '-f', 'ntfs', '-o', str(offset), image_path] if not inode else ['fls', '-f', 'ntfs', '-o', str(offset), image_path, inode]
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        
        for line in result.stdout.splitlines():
            if file_name in line:
                # 첫 번째 항목에 있는 inode 번호를 추출
                inode_number = line.split()[1].split(':')[0]
                print(f"{file_name}의 inode 번호: {inode_number}")
                return inode_number
    except subprocess.CalledProcessError as e:
        print(f"inode 번호를 찾는 중 오류 발생: {e}")
    return None

# Sleuth Kit의 icat 도구로 파일을 추출하는 함수
def extract_file_using_icat(image_path, offset, inode_number, output_file):
    """icat 도구로 파일을 추출하는 함수"""
    command = ['icat', '-o', str(offset), image_path, inode_number]
    
    try:
        with open(output_file, 'wb') as f:
            subprocess.run(command, check=True, stdout=f)
        print(f"파일 추출 완료: {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"파일 추출 중 오류 발생: {e}")

# MFT 및 UsnJrnl 파일 추출하는 함수
def parse_mft_and_usnjournal(image_path):
    """MFT 및 UsnJrnl 파일을 추출하는 함수"""
    
    # mmls를 사용해 Basic data partition의 시작 섹터를 가져옴
    partition_offset = get_partition_offset(image_path)
    
    if partition_offset is None:
        print("파티션 오프셋을 찾을 수 없습니다.")
        return
    
    # MFT 파일 추출
    mft_inode = get_inode_number(image_path, partition_offset, "$MFT")
    if mft_inode:
        extract_file_using_icat(image_path, partition_offset, mft_inode, 'extracted_mft.bin')
    else:
        print("MFT 파일을 찾을 수 없습니다.")
    
    # $LogFile 파일 추출
    # logfile_inode = get_inode_number(image_path, partition_offset, "$LogFile")
    # if logfile_inode:
        # extract_file_using_icat(image_path, partition_offset, logfile_inode, 'extracted_logfile.bin')
    # else:
        # print("$LogFile 파일을 찾을 수 없습니다.")
    
    # $Extend 디렉토리에서 UsnJrnl 확인 ($Extend 내부 탐색)
    extend_inode = get_inode_number(image_path, partition_offset, "$Extend")
    if extend_inode:
        usnjrnl_inode = get_inode_number(image_path, partition_offset, "$UsnJrnl", extend_inode)
        if usnjrnl_inode:
            # $UsnJrnl 파일 추출 (스트림 없이 추출)
            extract_file_using_icat(image_path, partition_offset, usnjrnl_inode, 'extracted_usnjrnl.bin')
        else:
            print("$UsnJrnl 파일을 찾을 수 없습니다.")
    else:
        print("$Extend 디렉토리를 찾을 수 없습니다.")

if __name__ == "__main__":
    # 디스크 이미지 경로
    image_path = r"F:\file_ext.raw"  # RAW 이미지 파일 경로

    # MFT 및 UsnJrnl 추출
    parse_mft_and_usnjournal(image_path)
