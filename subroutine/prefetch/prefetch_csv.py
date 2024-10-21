# -*- coding: euc-kr -*-
import os
import xml.etree.ElementTree as ET
import csv

def xml_to_csv(xml_file, csv_file):
    """XML ������ CSV ���Ϸ� ��ȯ�ϴ� �Լ�"""
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        # CSV ���� ����
        with open(csv_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["exe_path", "last_launch_time", "executable", "RunCount"])  # ��� �ۼ�

            for execution in root.findall('execution'):
                exe_path = execution.find('exe_path').text
                last_launch_time = execution.find('last_launch_time').text
                executable = execution.find('executable').text
                run_count = execution.find('RunCount').text
                writer.writerow([exe_path, last_launch_time, executable, run_count])

        print(f"CSV ������ ���������� �����Ǿ����ϴ�: {csv_file}")
    
    except ET.ParseError as e:
        print(f"XML �Ľ� ����: {e}")
    except Exception as e:
        print(f"CSV ��ȯ �� ���� �߻�: {e}")

def main():
    xml_file = r"..\..\output\artifact\prefetch\prefetch_analysis.xml"
    csv_file = r"..\..\output\artifact\prefetch\prefetch.csv"

    if not os.path.exists(xml_file):
        print(f"{xml_file} ������ �������� �ʽ��ϴ�.")
        return

    xml_to_csv(xml_file, csv_file)

if __name__ == "__main__":
    main()
