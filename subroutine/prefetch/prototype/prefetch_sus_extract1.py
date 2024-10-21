# -*- coding: utf-8 -*-
import xml.etree.ElementTree as ET
import csv
import os
import shutil
from datetime import datetime, timedelta
import re

def xml_to_csv_and_extract(xml_file, csv_file, prefetch_dir, suspicious_artifact_dir):
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"XML 파일에 오류가 있습니다: {e}")
        return

    anti_forensic_keywords = [
        r'(?i).*ccleaner.*', r'(?i).*cleaner.*', r'(?i).*eraser.*',
        r'(?i).*wiper.*', r'(?i).*scrubber.*', r'(?i).*delete.*',
        r'(?i).*remove.*', r'(?i).*destroy.*', r'(?i).*bleachbit.*'
    ]

    printed_executables = set()  # 이미 출력된 실행 파일을 저장하는 세트
    extracted_executables = set() # 이미 파싱된 아티팩트 파일을 저장하는 세트
    
    with open(csv_file, 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)

        if file.tell() == 0:
            writer.writerow(['Last Launch Time', 'Executable', 'Run Count', 'Path'])

        for execution in root.findall('execution'):
            last_launch_time = execution.find('last_launch_time').text
            executable = execution.find('executable').text
            run_count = int(execution.find('RunCount').text)
            exe_path = execution.find('exe_path').text

            # Ensure last_launch_time is valid
            if not last_launch_time or last_launch_time.strip() == "" or last_launch_time == "No Time Information":
                last_launch_time = "No Time Information"
                last_launch_time_dt = None
            else:
                try:
                    last_launch_time_dt = datetime.strptime(last_launch_time, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    print(f"잘못된 날짜 형식: {last_launch_time}")
                    last_launch_time_dt = None

            # Check executions within the last 10 minutes only if we have a valid datetime
            if last_launch_time_dt:
                start_time = last_launch_time_dt - timedelta(minutes=10)
                execution_times = [exec.find('last_launch_time').text for exec in root.findall('execution') if exec.find('executable').text == executable]
                
                # Filter valid datetime entries from execution_times
                valid_execution_times = []
                for time_str in execution_times:
                    if time_str and time_str.strip() != "" and time_str != "No Time Information":
                        try:
                            time_dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
                            valid_execution_times.append(time_dt)
                        except ValueError:
                            continue

                count_in_short_time = sum(1 for time in valid_execution_times if start_time <= time <= last_launch_time_dt)
            else:
                count_in_short_time = 0

            # Write to CSV if anti-forensic keyword matches and execution count is high
            if count_in_short_time > 10 and any(re.match(keyword, executable) for keyword in anti_forensic_keywords):
                writer.writerow([last_launch_time, executable, run_count, exe_path])

                # 의심스러운 동작이 이미 출력되지 않았으면 출력
                if executable not in printed_executables:
                    print(f"{executable} ({last_launch_time})가 의심스러운 동작을 수행했습니다.")
                    printed_executables.add(executable)  # 한번 출력된 파일 추가
                
                # Extract suspicious artifact (prefetch file) with matching hash
                suspicious_files = [f for f in os.listdir(prefetch_dir) if f.startswith(executable) and f.endswith('.pf')]
                
                if suspicious_files:
                    for suspicious_file in suspicious_files:
                        prefetch_file_path = os.path.join(prefetch_dir, suspicious_file)
                        destination_file = os.path.join(suspicious_artifact_dir, suspicious_file)
                        shutil.copy(prefetch_file_path, destination_file)
                        if executable not in extracted_executables:
                            print(f"의심스러운 파일 {suspicious_file} 추출 완료: {destination_file}")
                            extracted_executables.add(executable) # 한번 파싱된 파일 추가
                else:
                    print(f"의심스러운 파일을 찾을 수 없습니다: {executable}")

def main(xml_directory, csv_output_file, prefetch_dir, suspicious_artifact_dir):
    """주어진 XML 파일을 읽고 의심스러운 데이터를 CSV로 변환 및 의심스러운 파일 추출"""
    xml_file = os.path.join(xml_directory, 'prefetch_analysis.xml')
    
    if not os.path.exists(xml_file):
        print(f"{xml_file} 파일이 존재하지 않습니다.")
        return

    if not os.path.exists(suspicious_artifact_dir):
        os.makedirs(suspicious_artifact_dir)

    xml_to_csv_and_extract(xml_file, csv_output_file, prefetch_dir, suspicious_artifact_dir)

if __name__ == "__main__": 
    import sys
    if len(sys.argv) != 5:
        print("사용법: python prefetch_sus.py <xml_directory> <csv_output_file> <prefetch_dir> <suspicious_artifact_dir>")
    else:
        main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
