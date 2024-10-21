import os
import subprocess
import xml.etree.ElementTree as ET

# Prefetch 파일 목록을 가져오는 함수
def get_prefetch_files(prefetch_directory):
    """프리패치 디렉토리에서 .pf 파일 목록을 반환"""
    prefetch_files = []
    for root, dirs, files in os.walk(prefetch_directory):
        for file in files:
            if file.endswith('.pf'):
                prefetch_files.append(os.path.join(root, file))
    return prefetch_files

def uncomp_prefetch(prefetch_file):
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

    result = subprocess.run(command, shell=True, capture_output=True, text=True)

    if result.stderr:
        print("STDERR:", result.stderr)
    if result.stdout:
        print("STDOUT:", result.stdout)

# Prefetch 파일을 파싱하는 함수
def parse_prefetch(prefetch_file):
    try:
        with open(prefetch_file, 'rb') as f:
            filesize = os.path.getsize(prefetch_file)
            f.seek(16)
            executable_name = f.read(58).decode('utf-16le', errors='ignore').strip('\x00')

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

# XML 생성을 위한 함수
def generate_xml(last_launch_times, executable_name, run_count):
    xml_output = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml_output += '<prefetch>\n'
    for last_launch_time in last_launch_times:
        xml_output += '  <execution>\n'
        xml_output += '    <executable>%s</executable>\n' % executable_name
        xml_output += '    <last_launch_time>%s</last_launch_time>\n' % last_launch_time.strftime('%Y-%m-%d %H:%M:%S')
        xml_output += '    <RunCount>%d</RunCount>\n' % run_count
        xml_output += '  </execution>\n'
    xml_output += '</prefetch>'
    return xml_output

# Prefetch 분석 후 XML 파일 생성
def analyze_prefetch_and_generate_xml(prefetch_files, output_dir):
    for prefetch_file in prefetch_files:
        print(f"Analyzing: {prefetch_file}")
        uncomp_prefetch(prefetch_file)
        executable_name, last_launch_times, run_count = parse_prefetch(prefetch_file)
        if executable_name and last_launch_times:
            xml_data = generate_xml(last_launch_times, executable_name, run_count)
            xml_file_path = os.path.join(output_dir, f"{executable_name}.xml")
            with open(xml_file_path, "w", encoding="utf-8") as file:
                file.write(xml_data)
            print(f"XML saved to: {xml_file_path}")
        else:
            print(f"Error analyzing: {prefetch_file}")

# 메인 함수
def main():
    prefetch_directory = r"..\..\output\artifact\prefetch"  # 프리패치 파일 경로
    output_dir = r"..\..\output\artifact\suspicious_suspicious_file\prefetch"  # 결과 XML 저장 경로
    
    # Prefetch 디렉토리에서 .pf 파일 목록 가져오기
    prefetch_files = get_prefetch_files(prefetch_directory)
    
    if not prefetch_files:
        print("No prefetch files found.")
        return
    
    # 프리패치 파일 분석 후 XML 파일 생성
    analyze_prefetch_and_generate_xml(prefetch_files, output_dir)

if __name__ == "__main__":
    main()
