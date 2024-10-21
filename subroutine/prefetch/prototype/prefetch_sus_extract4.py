import xml.etree.ElementTree as ET
import csv
import os
import shutil
from datetime import datetime, timedelta
import re
import subprocess

def xml_to_csv_and_extract(xml_file, csv_file, prefetch_dir, suspicious_artifact_dir):
    try:
        # XML 파일을 읽어서 분석
        tree = ET.parse(xml_file)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"XML 파일에 오류가 있습니다: {e}")
        return

    # 안티 포렌식 키워드 목록 (정규 표현식)
    anti_forensic_keywords = [
        r'(?i).*ccleaner.*', r'(?i).*cleaner.*', r'(?i).*eraser.*',
        r'(?i).*wiper.*', r'(?i).*scrubber.*', r'(?i).*delete.*',
        r'(?i).*remove.*', r'(?i).*destroy.*', r'(?i).*bleachbit.*'
    ]

    processed_executables = set()  # 중복 방지를 위한 세트
    extracted_executables = set()  # 추출된 파일 추적

    # CSV 파일을 열고 분석 결과를 기록
    with open(csv_file, 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)

        # CSV 파일이 비어 있으면 헤더 추가
        if file.tell() == 0:
            writer.writerow(['Last Launch Time', 'Executable', 'Run Count', 'Path'])

        # XML의 실행 파일 기록을 반복 처리
        for execution in root.findall('execution'):
            last_launch_time = execution.find('last_launch_time').text
            executable = execution.find('executable').text
            run_count = int(execution.find('RunCount').text)
            exe_path = execution.find('exe_path').text

            if not last_launch_time or last_launch_time.strip() == "":
                last_launch_time = "No Time Information"
            else:
                try:
                    last_launch_time_dt = datetime.strptime(last_launch_time, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    print(f"잘못된 날짜 형식: {last_launch_time}")
                    continue

            # 중복 실행 파일인지 확인
            if executable in processed_executables:
                continue  # 이미 처리된 파일은 건너뜀

            # 실행 횟수와 시간 기반 필터링 (최근 10분간 실행 횟수)
            execution_times = [exec.find('last_launch_time').text for exec in root.findall('execution') if exec.find('executable').text == executable]
            valid_execution_times = []
            for time_str in execution_times:
                if time_str and time_str.strip() != "No Time Information":
                    try:
                        time_dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
                        valid_execution_times.append(time_dt)
                    except ValueError:
                        continue

            if last_launch_time_dt:
                start_time = last_launch_time_dt - timedelta(minutes=10)
                count_in_short_time = sum(1 for time in valid_execution_times if start_time <= time <= last_launch_time_dt)
            else:
                count_in_short_time = 0

            # 의심스러운 파일 처리 및 실행 횟수 출력
            if count_in_short_time > 10 and any(re.match(keyword, executable) for keyword in anti_forensic_keywords):
                print(f"{executable}가 10분 내에 {count_in_short_time}번 실행되었습니다.")

                # 의심스러운 실행 파일일 경우 Prefetch 파일 추출
                suspicious_files = [f for f in os.listdir(prefetch_dir) if executable.lower().replace('.exe', '') in f.lower() and f.endswith('.pf')]

                if suspicious_files:
                    for suspicious_file in suspicious_files:
                        prefetch_file_path = os.path.join(prefetch_dir, suspicious_file)
                        destination_file = os.path.join(suspicious_artifact_dir, suspicious_file)

                        print(f"추출하려는 Prefetch 파일: {prefetch_file_path}")

                        try:
                            shutil.copy(prefetch_file_path, destination_file)
                            # 모든 Prefetch 파일에 대해 추출 완료 메시지 출력
                            print(f"의심스러운 파일 {suspicious_file} 추출 완료: {destination_file}")
                            extracted_executables.add(executable)
                        except IOError as e:
                            print(f"파일 복사 중 오류 발생: {e}")
                else:
                    print(f"Prefetch 파일을 찾지 못했습니다: {executable}")

                # 분석된 실행 파일 정보를 CSV 파일에 기록
                writer.writerow([last_launch_time, executable, run_count, exe_path])
            else:
                print(f"의심스러운 키워드와 일치하지 않음: {executable}")

            # 중복 방지를 위해 파일을 처리 목록에 추가
            processed_executables.add(executable)

def main():
    # 경로 설정
    output_dir = os.path.join('..', '..', 'output', 'artifact', 'prefetch')  # XML 파일이 있는 디렉토리
    prefetch_dir = output_dir  # Prefetch 파일들이 있는 디렉토리
    sus_file_dir = r'..\..\output\suspicious_file\prefetch'  # 의심스러운 파일이 저장될 디렉토리
    sus_csv = r'..\..\output\suspicious_artifact\prefetch\prefetch_sus.csv'  # 분석 결과가 저장될 CSV 파일

    # XML 파일 경로
    xml_file = os.path.join(output_dir, 'prefetch_analysis.xml')

    # 분석 및 파일 추출 실행
    xml_to_csv_and_extract(xml_file, sus_csv, prefetch_dir, sus_file_dir)

if __name__ == "__main__":
    main()
