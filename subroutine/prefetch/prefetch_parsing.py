# -*- coding: utf-8 -*-
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
        
        for line in result.stdout.splitlines():
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
    print("fls 명령어 결과:")
    print(result.stdout)  # 결과를 직접 출력하여 확인
    
    # .pf 파일만 배열에 저장
    for line in result.stdout.splitlines():
        parts = line.split()
        if len(parts) > 1:
            # 파일 이름에 공백이 있을 수 있으므로 부분적으로 처리하지 않고 끝부분만 가져옴
            item_name = " ".join(parts[2:])  # 파일 이름이 여러 부분으로 나뉘어 있을 수 있음
            
            # 파일 유형을 제한하지 않고, .pf 확장자만으로 추출
            if item_name.endswith('.pf'):
                inode_number = parts[1].split(":")[0]  # inode 번호 추출
                pf_files.append((inode_number, item_name))
                print(f"파일: {item_name}")

    # .pf 파일 추출
    for inode, pf_file in pf_files:
        extract_pf_file(image_path, partition_offset, inode, pf_file, output_dir)
    
    return pf_files

# .pf 파일을 추출하는 함수
def extract_pf_file(image_path, partition_offset, inode, pf_file, output_dir):
    """icat을 사용하여 .pf 파일 추출"""
    try:
        # 출력 경로 설정
        output_path = os.path.join(output_dir, pf_file)
        
        # icat 명령어로 파일 추출
        command = ['icat', '-f', 'ntfs', '-o', str(partition_offset), image_path, inode]
        with open(output_path, 'wb') as f:
            result = subprocess.run(command, stdout=f, check=True)
        
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

# 이미지 파일 경로 및 출력 디렉토리 설정
image_path_directory = r"..\..\image_here"
first_disk_image_path = get_first_disk_image_path(image_path_directory)

#image_path = r"..\..\image_here\file_extract.E01"

output_dir = r"..\..\output\artifact\prefetch"  # 추출할 디렉토리 경로

# 이미지에서 Prefetch 파일 추출 실행
extract_prefetch_files_from_image(first_disk_image_path, output_dir)
