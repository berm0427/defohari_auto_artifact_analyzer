import os
import subprocess
import csv
import pandas as pd
import re
import pdb
import warnings
from concurrent.futures import ThreadPoolExecutor

# FutureWarning 무시 설정
warnings.simplefilter(action='ignore', category=FutureWarning)

mft_file = r'..\..\output\artifact\MFTJ\extracted_mft.bin'
usn_journal_file = r'..\..\output\artifact\MFTJ\extracted_usnjrnl.bin'

# mmls로 파티션 오프셋을 가져오는 함수
def get_partition_offset(image_path, partition_type="Basic data partition"):
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

# Sleuth Kit의 fls 도구로 inode 번호를 확인하는 함수
def get_inode_number(image_path, offset, file_name, inode=None):
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

# Sleuth Kit의 icat 도구로 파일을 추출하는 함수
def extract_file_using_icat(image_path, offset, inode_number, output_file):
    command = ['icat', '-o', str(offset), image_path, inode_number]
    try:
        with open(output_file, 'wb') as f:
            subprocess.run(command, check=True, stdout=f)
        print(f"파일 추출 완료: {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"파일 추출 중 오류 발생: {e}")

# MFT 및 UsnJrnl 파일 추출하는 함수
def parse_mft_and_usnjournal(image_path):
    partition_offset = get_partition_offset(image_path)
    if partition_offset is None:
        print("파티션 오프셋을 찾을 수 없습니다.")
        return
    
    # MFT 파일 추출
    mft_inode = get_inode_number(image_path, partition_offset, "$MFT")
    if mft_inode:
        extract_file_using_icat(image_path, partition_offset, mft_inode, mft_file)
    
    # $Extend 디렉토리에서 UsnJrnl 확인
    extend_inode = get_inode_number(image_path, partition_offset, "$Extend")
    if extend_inode:
        usnjrnl_inode = get_inode_number(image_path, partition_offset, "$UsnJrnl", extend_inode)
        if usnjrnl_inode:
            extract_file_using_icat(image_path, partition_offset, usnjrnl_inode, usn_journal_file)

# MFT 분석 함수
def analyze_mft(mft_file, output_file):
    if not os.path.exists(mft_file):
        raise FileNotFoundError(f"{mft_file} 파일을 찾을 수 없습니다.")
    command = ['python', r'analyzeMFT/analyzeMFT.py', '-f', mft_file, '-o', output_file, '--csv']
    subprocess.run(command, shell=True, check=True)
    print(f"MFT 분석 완료. 출력 파일: {output_file}")

# $UsnJrnl 분석 함수
def analyze_usn_journal(usn_journal_file, output_file):
    if not os.path.exists(usn_journal_file):
        raise FileNotFoundError(f"{usn_journal_file} 파일을 찾을 수 없습니다.")
    command = ['python', r'USN-Journal-Parser/usnparser/usn.py', '-f', usn_journal_file, '-o', output_file, '--csv']
    subprocess.run(command, shell=True, check=True)
    print(f"USN Journal 분석 완료. 출력 파일: {output_file}")

# 엑셀에 허용되지 않는 문자들을 필터링하는 함수
def clean_data_for_excel(df):
    def clean_string(value):
        if isinstance(value, str):
            return re.sub(r'[\000-\010]|[\013-\014]|[\016-\037]', '', value)
        return value
    return df.applymap(clean_string)

def process_chunk(chunk):
    return clean_data_for_excel(chunk)

def save_to_excel_parallel(mft_data, usn_data, output_excel):
    with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
        chunk_size = 10000

        # MFT 파일 처리
        mft_chunk_iter = pd.read_csv(mft_data, chunksize=chunk_size, low_memory=False)
        with ThreadPoolExecutor() as executor:
            for cleaned_chunk in executor.map(process_chunk, mft_chunk_iter):
                cleaned_chunk.to_excel(writer, sheet_name='MFT Analysis', index=False, header=False)

        # USN 파일 처리
        usn_chunk_iter = pd.read_csv(usn_data, chunksize=chunk_size, low_memory=False)
        with ThreadPoolExecutor() as executor:
            for cleaned_chunk in executor.map(process_chunk, usn_chunk_iter):
                cleaned_chunk.to_excel(writer, sheet_name='USN Journal Analysis', index=False, header=False)

    print(f"엑셀 파일 저장 완료: {output_excel}")
    
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


   

if __name__ == "__main__":
    # 이미지 파일 경로 및 출력 디렉토리 설정
    image_path_directory = r"..\..\image_here"
    first_disk_image_path = get_first_disk_image_path(image_path_directory)
    
    #image_path = r"..\..\image_here\file_extract.E01"
    mft_output_csv = r'..\..\output\artifact\MFTJ\mft_output.csv'
    usn_output_csv = r'..\..\output\artifact\MFTJ\usn_output.csv'
    output_excel = r'..\..\output\artifact\MFTJ\disk_analysis_results.xlsx'

    # 1. MFT, UsnJrnl 추출
    parse_mft_and_usnjournal(first_disk_image_path)

    # 2. MFT 분석
    analyze_mft(mft_file, mft_output_csv)

    # 3. USN Journal 분석
    analyze_usn_journal(usn_journal_file, usn_output_csv)

    # 4. 분석 결과를 엑셀 파일로 저장 (MFT와 USN Journal만)
    save_to_excel_parallel(mft_output_csv, usn_output_csv, output_excel)
