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

'''
def run_hive(image_path):
    """Step 0: web_hive_parsing_Log_num.py 실행, 파싱한 하이브 파일을 저장"""
    subprocess.run(['python', 'web_hive_parsing_Log_num.py', image_path], check=True)
'''

def run_web_parsing():
    """Step 1: web_parsing.py 실행, 파싱한 웹 아티팩트 파일을 저장"""
    subprocess.run(['python', 'web_parsing.py'], check=True)

def run_web_analysis_with_xml():
    """Step 2: web_artifact.py 실행 후 XML로 결과 저장"""
    subprocess.run(['python', 'web_artifact.py'], check=True)

def run_web_csv():
    """Step 3: web_csv.py 실행 후 CSV 출력"""
    subprocess.run(['python', 'web_csv.py'], check=True)


def run_web_sus_analysis():
    """Step 4: web_csv_sus.py 실행 후 의심스러운 로그를 CSV로 출력"""
    subprocess.run(['python', 'web_csv_sus.py'], check=True)

def run_web_sus_ext_analysis():
    """Step 4: web_sus_extract.py 실행 후 의심스러운 파일을 추출"""
    subprocess.run(['python', 'web_sus_extract.py'], check=True)


def main(image_path):
    
    '''
    # 1. 하이브 파일 파싱 (유저 정보 추출) <--- defohari로 이관
    output_dir = os.path.join('..', '..', 'output', 'artifact', 'web')  # 상대 경로로 설정
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    run_hive(image_path)
    '''
    
    # 2. 웹 아티팩트 분석
    run_web_parsing()
    run_web_analysis_with_xml()
    
    # 3. 분석 결과를 CSV로 출력
    run_web_csv()
    
    # 4. 의심스러운 웹 흔적을 분석하여 CSV 및 파일 출력
    sus_output_dir = os.path.join('..', '..', 'output', 'suspicious_artifact', 'web')
    if not os.path.exists(sus_output_dir):
        os.makedirs(sus_output_dir)   
    run_web_sus_analysis()
    
    # 5. 의심스러운 파일 추출
    run_web_sus_ext_analysis()
    
if __name__ == "__main__":
    image_path_directory = r"..\..\image_here"
    first_disk_image_path = get_first_disk_image_path(image_path_directory)
    main(first_disk_image_path)
