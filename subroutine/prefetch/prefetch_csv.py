# -*- coding: euc-kr -*-
import os
import xml.etree.ElementTree as ET
import csv

def xml_to_csv(xml_file, csv_file):
    """XML 파일을 CSV 파일로 변환하는 함수"""
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        # CSV 파일 생성
        with open(csv_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["exe_path", "last_launch_time", "executable", "RunCount"])  # 헤더 작성

            for execution in root.findall('execution'):
                exe_path = execution.find('exe_path').text
                last_launch_time = execution.find('last_launch_time').text
                executable = execution.find('executable').text
                run_count = execution.find('RunCount').text
                writer.writerow([exe_path, last_launch_time, executable, run_count])

        print(f"CSV 파일이 성공적으로 생성되었습니다: {csv_file}")
    
    except ET.ParseError as e:
        print(f"XML 파싱 오류: {e}")
    except Exception as e:
        print(f"CSV 변환 중 오류 발생: {e}")

def main():
    xml_file = r"..\..\output\artifact\prefetch\prefetch_analysis.xml"
    csv_file = r"..\..\output\artifact\prefetch\prefetch.csv"

    if not os.path.exists(xml_file):
        print(f"{xml_file} 파일이 존재하지 않습니다.")
        return

    xml_to_csv(xml_file, csv_file)

if __name__ == "__main__":
    main()
