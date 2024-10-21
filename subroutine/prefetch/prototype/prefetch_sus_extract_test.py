# -*- coding: utf-8 -*-
import xml.etree.ElementTree as ET
import csv
import os
import shutil
from datetime import datetime, timedelta
import re

def xml_to_csv_and_extract(xml_file, csv_file, prefetch_dir, suspicious_artifact_dir):
    try:
        # XML 파일을 부분적으로 읽기 위해 iterparse 사용
        context = ET.iterparse(xml_file, events=("start", "end"))
        context = iter(context)
        _, root = next(context)  # XML 파일의 루트를 얻음
    except ET.ParseError as e:
        print(f"XML 파일에 오류가 있습니다: {e}")
        return

    anti_forensic_keywords = [
        re.compile(r'(?i).*ccleaner.*'), re.compile(r'(?i).*cleaner.*'),
        re.compile(r'(?i).*eraser.*'), re.compile(r'(?i).*wiper.*'),
        re.compile(r'(?i).*scrubber.*'), re.compile(r'(?i).*delete.*'),
        re.compile(r'(?i).*remove.*'), re.compile(r'(?i).*destroy.*'),
        re.compile(r'(?i).*bleachbit.*')
    ]

    printed_executables = set()  # 이미 출력된 실행 파일을 저장하는 세트
    extracted_executables = set()  # 이미 파싱된 아티팩트 파일을 저장하는 세트
    
    # 미리 파일 이름과 경로를 딕셔너리로 저장 (prefetch 파일 캐싱)
    prefetch_files = {f: os.path.join(prefetch_dir, f) for f in os.listdir(prefetch_dir) if f.endswith('.pf')}
    
    # CSV 파일을 한번에 열고 모든 데이터를 모아서 작성하는 방식으로 변경
    csv_rows = []

    for event, elem in context:
        if event == "end" and elem.tag == "execution":
            last_launch_time = elem.find('last_launch_time').text if elem.find('last_launch_time') is not None else None
            executable = elem.find('executable').text if elem.find('executable') is not None else None
            run_count = elem.find('RunCount').text if elem.find('RunCount') is not None else None
            exe_path = elem.find('exe_path').text if elem.find('exe_path') is not None else None

            # Check if critical fields are None
            if executable is None or run_count is None:
                continue  # 필요한 정보가 없으면 스킵

            run_count = int(run_count)

            # Ensure last_launch_time is valid
            if not last_launch_time or last_launch_time.strip() == "" or last_launch_time == "No Time Information":
                last_launch_time_dt = None
            else:
                try:
                    last_launch_time_dt = datetime.strptime(last_launch_time, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    last_launch_time_dt = None

            # Check executions within the last 10 minutes only if we have a valid datetime
            if last_launch_time_dt:
                start_time = last_launch_time_dt - timedelta(minutes=10)
                execution_times = []
                for sibling in root.findall('execution'):
                    sibling_executable = sibling.find('executable').text if sibling.find('executable') is not None else None
                    if sibling_executable == executable:
                        time_str = sibling.find('last_launch_time').text
                        if time_str and time_str.strip() != "" and time_str != "No Time Information":
                            try:
                                time_dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
                                execution_times.append(time_dt)
                            except ValueError:
                                continue
                
                count_in_short_time = sum(1 for time in execution_times if start_time <= time <= last_launch_time_dt)
            else:
                count_in_short_time = 0

            # Write to CSV if anti-forensic keyword matches and execution count is high
            if count_in_short_time > 10 and any(keyword.match(executable) for keyword in anti_forensic_keywords):
                csv_rows.append([last_launch_time, executable, run_count, exe_path])

                # 의심스러운 동작이 이미 출력되지 않았으면 출력
                if executable not in printed_executables:
                    print(f"{executable} ({last_launch_time})가 의심스러운 동작을 수행했습니다.")
                    printed_executables.add(executable)

                # Extract suspicious artifact (prefetch file) with matching hash
                matching_prefetch_files = [f for f in prefetch_files if f.startswith(executable)]
                
                if matching_prefetch_files:
                    for suspicious_file in matching_prefetch_files:
                        destination_file = os.path.join(suspicious_artifact_dir, suspicious_file)
                        shutil.copy(prefetch_files[suspicious_file], destination_file)
                        if executable not in extracted_executables:
                            print(f"의심스러운 파일 {suspicious_file} 추출 완료: {destination_file}")
                            extracted_executables.add(executable)
                else:
                    print(f"의심스러운 파일을 찾을 수 없습니다: {executable}")
            
            # 메모리 절약을 위해 사용한 XML 요소 제거
            elem.clear()

    # CSV 파일에 한번에 쓰기
    with open(csv_file, 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        if file.tell() == 0:  # 파일이 비어 있으면 헤더 추가
            writer.writerow(['Last Launch Time', 'Executable', 'Run Count', 'Path'])
        writer.writerows(csv_rows)

def main(xml_directory, csv_output_file, prefetch_dir, suspicious_artifact_dir):
    """주어진 XML 파일을 읽고 의심스러운 데이터를 CSV로 변환 및 의심스러운 파일 추출"""
    xml_file = os.path.join(xml_directory, 'prefetch_analysis.xml')
    
    if not os.path.exists(xml_file):
        # print(f"{xml_file} 파일이 존재하지 않습니다.")
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
