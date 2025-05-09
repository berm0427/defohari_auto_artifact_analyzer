# coding=EUC-KR
import os
import struct
from datetime import datetime, timedelta
import pytz
import xml.etree.ElementTree as ET
import subprocess

def uncomp_prefetch(prefetch_file):
    # 외부 스크립트 경로 확인이 필요할 수 있음
    script_path = "./win10de.py"  # 현재 디렉토리 또는 전체 경로 지정
    command = ["python", script_path, prefetch_file, prefetch_file]
    
    try:
        with open(prefetch_file, 'rb') as f:
            header = f.read(8)
            if header[0:3] != b'MAM':  # 3바이트로 수정
                print("Not a compressed prefetch file.")
                return None, None
    except FileNotFoundError:
        print("File not found:", prefetch_file)
        return None, None

    # subprocess.run을 사용하여 외부 프로세스 실행
    result = subprocess.run(command, shell=True, capture_output=True, text=True)

    # 실행 결과와 에러 출력
    if result.stderr:
        print("STDERR:", result.stderr)
    if result.stdout:
        print("STDOUT:", result.stdout)

def filetime_to_dt(filetime):
    if filetime < 0:
        return "Invalid file time"
    utc_time = datetime(1601, 1, 1) + timedelta(microseconds=filetime // 10)
    korea_timezone = pytz.timezone('Asia/Seoul')
    korea_time = utc_time.replace(tzinfo=pytz.utc).astimezone(korea_timezone)
    return korea_time

def parse_prefetch(prefetch_file):
    try:
        with open(prefetch_file, 'rb') as f:
            filesize = os.path.getsize(prefetch_file)
            f.seek(16)
            executable_name = f.read(58).decode('utf-16le').strip('\x00')

            last_launch_times = []
            f.seek(128)
            for _ in range(8):
                if f.tell() + 8 > filesize:
                    raise ValueError("Attempt to read beyond file size.")
                raw_time = f.read(8)
                if len(raw_time) == 8:
                    file_time = struct.unpack('<Q', raw_time)[0]
                    last_launch_times.append(filetime_to_dt(file_time))

            f.seek(200)
            if f.tell() + 4 > filesize:
                raise ValueError("Attempt to read beyond file size.")
            run_count = struct.unpack('<I', f.read(4))[0]

            return executable_name, last_launch_times, run_count

    except Exception as e:
        print("Error parsing prefetch file:", e)
        return None, None, None

def generate_xml(executable_name, last_launch_times, run_count):
    root = ET.Element("PrefetchData")
    ET.SubElement(root, "ExecutableName").text = executable_name
    ET.SubElement(root, "RunCount").text = str(run_count)
    
    launches = ET.SubElement(root, "LaunchTimes")
    for launch_time in last_launch_times:
        ET.SubElement(launches, "LaunchTime").text = launch_time.strftime('%Y-%m-%d %H:%M:%S')
    
    tree = ET.ElementTree(root)
    tree.write("output.xml")
    ET.dump(root)  # This prints the XML to the console

def main():
    prefetch_file = '7ZFM.EXE-1E4F7C11.pf'
    uncomp_prefetch(prefetch_file)
    executable_name, last_launch_times, run_count = parse_prefetch(prefetch_file)
    if executable_name and last_launch_times:
        generate_xml(executable_name, last_launch_times, run_count)

if __name__ == "__main__":
    main()

