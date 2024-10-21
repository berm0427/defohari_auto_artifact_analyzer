
# -*- coding: utf-8 -*-
import subprocess
import os
import sys
import argparse

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
        return found_inodes
    except subprocess.CalledProcessError as e:
        print(f"inode 번호를 찾는 중 오류 발생: {e}")
    return []

# 디렉토리 inode 번호만 가져오는 함수
def get_inode_number_for_directory(image_path, offset, file_name, inode=None):
    """fls 도구 디렉토리의 inode 번호를 가져오는 함수"""
    try:
        command = ['fls', '-f', 'ntfs', '-D', '-o', str(offset), image_path] if not inode else ['fls', '-f', 'ntfs', '-D', '-o', str(offset), image_path, inode]
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        
        for line in result.stdout.splitlines():
            if file_name in line:
                inode_number = line.split()[1].split(':')[0]
                print(f"{file_name}의 inode 번호: {inode_number}")
                return inode_number
    except subprocess.CalledProcessError as e:
        print(f"inode 번호를 찾는 중 오류 발생: {e}")
    return None

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

# SAM 및 SYSTEM 하이브와 로그 파일들을 추출하는 함수
def extract_hives(image_path, output_dir):
    """디스크 이미지에서 SAM 및 SYSTEM 하이브 파일을 추출"""
    
    # 파티션 오프셋을 가져옴
    partition_offset = get_partition_offset(image_path)
    
    if partition_offset is None:
        print("파티션 오프셋을 찾을 수 없습니다.")
        return
    
    # Windows 디렉토리 inode 가져오기
    windows_inode = get_inode_number(image_path, partition_offset, "Windows")
    
    if not windows_inode:
        print("Windows 디렉토리를 찾을 수 없습니다.")
        return
    
    # System32 디렉토리 inode 가져오기
    system32_inode = get_inode_number(image_path, partition_offset, "System32", windows_inode[0])
    
    if not system32_inode:
        print("System32 디렉토리를 찾을 수 없습니다.")
        return
    
    # config 디렉토리 inode 가져오기
    config_inode = get_inode_number_for_directory(image_path, partition_offset, "config", system32_inode[0])
    
    if not config_inode:
        print("config 디렉토리를 찾을 수 없습니다.")
        return
    
    # SAM 하이브 파일 및 로그 파일 inode 가져오기
    sam_inodes = get_inode_number(image_path, partition_offset, "SAM", config_inode)
    sam_log_inodes = get_inode_number(image_path, partition_offset, "SAM.LOG", config_inode)  # LOG 파일도 확인
    
    # SYSTEM 하이브 파일 및 로그 파일 inode 가져오기
    system_inodes = get_inode_number(image_path, partition_offset, "SYSTEM", config_inode)
    system_log_inodes = get_inode_number(image_path, partition_offset, "SYSTEM.LOG", config_inode)  # LOG 파일도 확인

    # SAM 및 SAM.LOG* 파일들 추출 (LOG 파일에 번호 부여)
    for i, inode in enumerate(sam_inodes):
        extract_file(image_path, partition_offset, inode, output_dir, f"SAM")
    for i, inode in enumerate(sam_log_inodes, 1):
        extract_file(image_path, partition_offset, inode, output_dir, f"SAM.LOG{i}")

    # SYSTEM 및 SYSTEM.LOG* 파일들 추출 (LOG 파일에 번호 부여)
    for i, inode in enumerate(system_inodes):
        extract_file(image_path, partition_offset, inode, output_dir, f"SYSTEM")
    for i, inode in enumerate(system_log_inodes, 1):
        extract_file(image_path, partition_offset, inode, output_dir, f"SYSTEM.LOG{i}")

# 스크립트 실행 부분
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="디스크 이미지에서 SAM 및 SYSTEM 하이브 파일 추출")
    parser.add_argument("image", help="디스크 이미지 파일 경로 (예: image.dd, image.E01)")
    parser.add_argument("-o", "--output", help="출력 디렉토리", default="extracted_hives")
    args = parser.parse_args()
    
    image_path = args.image
    output_dir = args.output
    
    if not os.path.exists(image_path):
        print(f"디스크 이미지 파일이 존재하지 않습니다: {image_path}")
        sys.exit(1)
    
    extract_hives(image_path, output_dir)
