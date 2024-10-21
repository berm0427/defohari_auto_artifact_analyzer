# -*- coding: utf-8 -*-
import os
import struct
from datetime import datetime, timedelta
import pytz
import xml.etree.ElementTree as ET
import subprocess
import re

def uncomp_prefetch(prefetch_file):
    """압축된 prefetch 파일을 해제"""
    script_path = "./win10de.py"  # 현재 디렉토리 또는 전체 경로 지정
    command = ["python", script_path, prefetch_file, prefetch_file]

    try:
        with open(prefetch_file, 'rb') as f:
            header = f.read(8)
            if header[0:3] != b'MAM':  # 압축 파일 확인 (앞 3바이트 확인)
                print(f"[WARN] {prefetch_file}: 압축되지 않은 prefetch 파일입니다.")
                return prefetch_file  # 압축되지 않은 파일도 처리하도록 반환
    except FileNotFoundError:
        print(f"[ERROR] {prefetch_file}: 파일을 찾을 수 없습니다.")
        return None

    # 압축 해제 시도
    result = subprocess.run(command, shell=True, capture_output=True, text=True)

    if result.stderr:
        print(f"[ERROR] {prefetch_file}: 해제 오류 - {result.stderr}")
        return prefetch_file  # 압축 해제 실패 시 원본 파일로 계속 진행
    if result.stdout:
        print(f"[INFO] {prefetch_file}: {result.stdout}")

    return prefetch_file  # 성공 시에도 파일을 반환

def filetime_to_dt(filetime):
    """Windows FILETIME 값을 날짜 시간으로 변환"""
    if filetime < 0:
        return "Invalid file time"
    try:
        utc_time = datetime(1601, 1, 1) + timedelta(microseconds=filetime // 10)
        korea_timezone = pytz.timezone('Asia/Seoul')
        korea_time = utc_time.replace(tzinfo=pytz.utc).astimezone(korea_timezone)
        return korea_time if korea_time.year > 1601 else ""
    except OverflowError:
        print("[WARN] 파일 시간이 유효하지 않습니다.")
        return "Invalid file time"

def parse_prefetch(prefetch_file):
    """Prefetch 파일을 파싱하여 실행 정보 추출"""
    try:
        with open(prefetch_file, 'rb') as f:
            filesize = os.path.getsize(prefetch_file)
            f.seek(16)
            executable_name = f.read(58).decode('utf-16le', errors='ignore').strip('\x00')

            last_launch_times = []
            f.seek(128)
            for _ in range(8):
                if f.tell() + 8 > filesize:
                    raise ValueError("[ERROR] 파일 크기를 초과하여 읽으려 합니다.")
                raw_time = f.read(8)
                if len(raw_time) == 8:
                    file_time = struct.unpack('<Q', raw_time)[0]
                    last_launch_times.append(filetime_to_dt(file_time))

            f.seek(200)
            if f.tell() + 4 > filesize:
                raise ValueError("[ERROR] 파일 크기를 초과하여 읽으려 합니다.")
            run_count = struct.unpack('<I', f.read(4))[0]

            # 실행 파일 경로 읽기
            f.seek(0x64)
            path_offset = struct.unpack('<I', f.read(4))[0]
            f.seek(0x68)
            path_length = struct.unpack('<I', f.read(4))[0]
            f.seek(path_offset)
            executable_path_bytes = f.read(path_length)
            
            try:
                executable_path = executable_path_bytes.decode('utf-16le', errors='ignore').strip('\x00')
            except UnicodeDecodeError:
                try:
                    executable_path = executable_path_bytes.decode('utf-8', errors='ignore').strip('\x00')
                except UnicodeDecodeError:
                    executable_path = executable_path_bytes.decode('latin1', errors='ignore').strip('\x00')

            executable_paths = executable_path.split('\x00')
            executable_paths = [path for path in executable_paths if path]

            return executable_name, last_launch_times, run_count, executable_paths

    except Exception as e:
        print(f"[ERROR] {prefetch_file}: Prefetch 파일 파싱 중 오류 발생 - {e}")
        return None, None, None, None

def escape_xml_characters(data):
    """XML에서 특수 문자를 처리"""
    return re.sub(r'[^\x09\x0A\x0D\x20-\x7E]', '', data)

def generate_xml(last_launch_times, executable_name, run_count, executable_paths):
    """XML 데이터를 생성"""
    xml_output = ''
    for last_launch_time in last_launch_times:
        for executable_path in executable_paths:
            xml_output += '  <execution>\n'
            xml_output += '    <exe_path>%s</exe_path>\n' % escape_xml_characters(executable_path)
            if isinstance(last_launch_time, datetime):
                xml_output += '    <last_launch_time>%s</last_launch_time>\n' % last_launch_time.strftime('%Y-%m-%d %H:%M:%S')
            else:
                xml_output += '    <last_launch_time>%s</last_launch_time>\n' % last_launch_time
            xml_output += '    <executable>%s</executable>\n' % escape_xml_characters(executable_name)
            xml_output += '    <RunCount>%d</RunCount>\n' % run_count
            xml_output += '  </execution>\n'
    return xml_output

def process_all_prefetch_files(prefetch_dir, output_xml_file):
    """주어진 디렉토리에서 모든 .pf 파일을 처리하여 XML 파일로 출력"""
    with open(output_xml_file, "w", encoding="utf-8") as file:
        # XML 시작 태그 추가
        file.write('<?xml version="1.0" encoding="UTF-8"?>\n<prefetch>\n')
        print("[INFO] XML 시작 태그 작성 완료")

        for root, _, files in os.walk(prefetch_dir):
            for pf_file in files:
                if pf_file.endswith(".pf"):
                    prefetch_file_path = os.path.join(root, pf_file)
                    uncomp_prefetch(prefetch_file_path)
                    executable_name, last_launch_times, run_count, executable_paths = parse_prefetch(prefetch_file_path)
                    if executable_name and last_launch_times:
                        xml_data = generate_xml(last_launch_times, executable_name, run_count, executable_paths)
                        file.write(xml_data)
                        print(f"[INFO] {pf_file} 처리 완료 및 XML에 기록.")
                    else:
                        print(f"[ERROR] {pf_file} 처리 실패.")

        # XML 종료 태그 추가
        file.write('</prefetch>\n')
        print("[INFO] XML 종료 태그 작성 완료")

def main(prefetch_dir):
    # XML 파일로 출력할 경로 설정
    output_xml_file = os.path.join(prefetch_dir, "prefetch_analysis.xml")
    # 모든 .pf 파일 처리 및 XML 생성
    process_all_prefetch_files(prefetch_dir, output_xml_file)

if __name__ == "__main__":
    # Prefetch 파일이 저장된 디렉토리 경로
    prefetch_dir = r"..\..\output\artifact\prefetch"
    main(prefetch_dir)