import os
import subprocess
import csv
import pandas as pd
import re

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

# CSV 데이터를 Excel로 저장
def save_to_excel(mft_data, usn_data, output_excel):
    with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
        mft_df = pd.read_csv(mft_data, low_memory=False)
        usn_df = pd.read_csv(usn_data, low_memory=False)
        
        mft_df_clean = clean_data_for_excel(mft_df)
        usn_df_clean = clean_data_for_excel(usn_df)
        
        mft_df_clean.to_excel(writer, sheet_name='MFT Analysis', index=False)
        usn_df_clean.to_excel(writer, sheet_name='USN Journal Analysis', index=False)
    
    print(f"엑셀 파일 저장 완료: {output_excel}")
   

if __name__ == "__main__":
    image_path = r"F:\file_extract.E01"
    mft_output_csv = r'..\..\output\artifact\MFTJ\mft_output.csv'
    usn_output_csv = r'..\..\output\artifact\MFTJ\usn_output.csv'
    output_excel = r'..\..\output\artifact\MFTJ\disk_analysis_results.xlsx'

    # 1. MFT, UsnJrnl 추출
    parse_mft_and_usnjournal(image_path)

    # 2. MFT 분석
    analyze_mft(mft_file, mft_output_csv)

    # 3. USN Journal 분석
    analyze_usn_journal(usn_journal_file, usn_output_csv)

    # 4. 분석 결과를 엑셀 파일로 저장 (MFT와 USN Journal만)
    save_to_excel(mft_output_csv, usn_output_csv, output_excel)
