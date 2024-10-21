# coding=UTF-8
import subprocess
import os

# 스크립트가 있는 디렉토리로 작업 디렉토리 변경
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

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

def run_prefetch_parsing(image_path, output_dir):
    """Step 1: prefetch_parsing.py 실행, 파싱한 프리패치 파일을 저장"""
    subprocess.run(['python', 'prefetch_parsing.py', image_path, output_dir], check=True)

def run_prefetch_analysis_with_xml(prefetch_dir):
    """Step 2: prefetch_with_xml_reference_path.py 실행 후 XML로 결과 저장"""
    subprocess.run(['python', 'prefetch_with_xml_reference_path.py', prefetch_dir], check=True)

def run_prefetch_csv(csv_output_dir):
    """Step 3: prefetch_csv.py 실행 후 CSV 출력"""
    subprocess.run(['python', 'prefetch_csv.py', csv_output_dir], check=True)

def run_prefetch_sus_ext_analysis():
    """Step 4: prefetch_sus.py 실행 후 의심스러운 프리패치 파일을 출력"""
    subprocess.run(['python', 'prefetch_sus_extract.py'], check=True)


def main(image_path):
    # 1. 프리패치 파싱 및 추출
    output_dir = os.path.join('..', '..', 'output', 'artifact', 'prefetch')  # 상대 경로로 설정
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    run_prefetch_parsing(image_path, output_dir)
    
    # 2. 파싱한 프리패치 분석 (XML 생성)
    run_prefetch_analysis_with_xml(output_dir)
    
    # 3. 분석 결과를 CSV로 출력
    csv_output_dir = os.path.join('..', '..', 'output', 'artifact', 'prefetch')  # CSV 파일 경로 변경
    if not os.path.exists(csv_output_dir):
        os.makedirs(csv_output_dir)
    run_prefetch_csv(csv_output_dir)
    
    # 4. 의심스러운 프리패치 파일을 분석하여 CSV 및 .pf 파일 출력
    sus_output_dir = os.path.join('..', '..', 'output', 'suspicious_artifact', 'prefetch')  # 의심스러운 파일 경로 변경
    if not os.path.exists(sus_output_dir):
        os.makedirs(sus_output_dir)
    run_prefetch_sus_ext_analysis()

if __name__ == "__main__":
    image_path_directory = r"..\..\image_here"
    first_disk_image_path = get_first_disk_image_path(image_path_directory)
    main(first_disk_image_path)
