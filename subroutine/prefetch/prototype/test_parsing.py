# -*- coding: utf-8 -*-
import subprocess
import os
import re

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
            print(f"fls 출력 라인: {line}")  # fls 출력 확인을 위한 로그 추가
            if file_name in line:
                inode_number = line.split()[1].split(':')[0]
                print(f"{file_name}의 inode 번호: {inode_number}")
                return inode_number
    except subprocess.CalledProcessError as e:
        print(f"inode 번호를 찾는 중 오류 발생: {e}")
    return None


# Prefetch 디렉토리 내 .pf 파일을 배열에 저장하고 추출하는 함수
def list_and_extract_pf_files(image_path, partition_offset, prefetch_inode, output_dir):
    """C:\\Windows\\Prefetch 디렉토리의 .pf 파일을 배열에 저장하고 추출하는 함수"""
    
    # .pf 파일을 저장할 배열
    pf_files = []

    # Prefetch 디렉토리 내 파일과 하위 디렉토리 나열
    command = ['fls', '-f', 'ntfs', '-o', str(partition_offset), image_path, prefetch_inode]
    result = subprocess.run(command, capture_output=True, text=True, check=True)

    # fls 명령어 결과 출력
    print("\n=== fls 명령어 결과 ===")
    print(result.stdout)  # 결과를 직접 출력하여 확인

    # 정규 표현식을 사용해 inode 번호와 파일 이름 추출
    pattern = re.compile(r'(\d+-\d+-\d+):\s+(.*\.pf)')
    
    for line in result.stdout.splitlines():
        match = pattern.search(line)
        if match:
            inode_number = match.group(1)  # inode 번호 추출
            item_name = match.group(2)     # 파일 이름 추출
            pf_files.append((inode_number, item_name))
            print(f"발견된 파일: {item_name} (inode: {inode_number})")
                
    # .pf 파일이 발견된 경우 파일 추출
    if pf_files:
        print(f"\n총 {len(pf_files)}개의 .pf 파일 발견")
        print("\n=== 파일 추출 시작 ===")
        for idx, (inode, pf_file) in enumerate(pf_files, 1):
            print(f"[{idx}/{len(pf_files)}] 파일 추출 중: {pf_file}")
            extract_pf_file(image_path, partition_offset, inode, pf_file, output_dir)
        print("\n=== 모든 파일 추출 완료 ===\n")
    else:
        print("\n추출할 .pf 파일이 없습니다.\n")
    
    return pf_files

# .pf 파일을 추출하는 함수
def extract_pf_file(image_path, partition_offset, inode, pf_file, output_dir):
    """icat을 사용하여 .pf 파일 추출"""
    try:
        # 출력 경로 설정
        output_path = os.path.join(output_dir, pf_file)
        
        # icat 명령어로 파일 추출
        command = ['icat', '-f', 'ntfs', '-o', str(partition_offset), image_path, inode]
        
        # 명령어 로그 추가
        print(f"icat 명령어 실행: {' '.join(command)}")
        
        with open(output_path, 'wb') as f:
            subprocess.run(command, stdout=f, check=True)
        
        print(f"파일 추출 완료: {pf_file}")
    except subprocess.CalledProcessError as e:
        print(f"파일 추출 중 오류 발생: {e}")
        
# 메인 함수: 전체 작업 수행
def extract_prefetch_files_from_image(image_path, output_dir):
    """이미지 파일에서 Prefetch 파일을 추출하는 함수"""
    
    # Basic data partition의 오프셋을 가져옴
    partition_offset = get_partition_offset(image_path)
    
    if partition_offset is None:
        print("파티션 오프셋을 찾을 수 없습니다.")
        return
    
    # Windows 디렉토리 inode 가져오기
    windows_inode = get_inode_number(image_path, partition_offset, "Windows")
    
    if windows_inode is None:
        print("Windows 디렉토리를 찾을 수 없습니다.")
        return
    
    # Prefetch 디렉토리 inode 가져오기
    prefetch_inode = get_inode_number(image_path, partition_offset, "Prefetch", windows_inode)
    
    if prefetch_inode is None:
        print("Prefetch 디렉토리를 찾을 수 없습니다.")
        return
    
    # Prefetch 디렉토리에서 .pf 파일 목록 배열에 저장 및 추출
    pf_files = list_and_extract_pf_files(image_path, partition_offset, prefetch_inode, output_dir)
    
    print(f"총 {len(pf_files)}개의 .pf 파일이 추출되었습니다.")

# 이미지 파일 경로 및 출력 디렉토리 설정
image_path = r"F:\file_extract_torrent.E01"
output_dir = r"..\..\output\artifact\prefetch"  # 추출할 디렉토리 경로

# 이미지에서 Prefetch 파일 추출 실행
extract_prefetch_files_from_image(image_path, output_dir)
