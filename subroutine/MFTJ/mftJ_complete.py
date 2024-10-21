# coding=UTF-8
import subprocess
import os

# 스크립트가 있는 디렉토리로 작업 디렉토리 변경
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

def run_MFTJ_parsing():
    """Step 1: mftJ_csv.py 실행, 파싱한 MFT 및 유저저널 파일을 저장 및 분석 csv로 추출 (통합화된 xlsx 파일도 있음)"""
    subprocess.run(['python', 'mftJ_csv.py'], check=True)

def run_MFTJ_sus_analysis():
    """Step 2: MFT_sus.py 실행 후 의심스러운 흔적 리스트를 CSV로 및 xml 출력"""
    subprocess.run(['python', 'MFTJ_sus.py'], check=True)


def main():
    # 1. mftJ_csv.py 실행, 파싱한 MFT 및 유저저널 파일을 저장 및 분석 csv로 추출 (통합화된 xlsx 파일도 있음)
    output_dir = os.path.join('..', '..', 'output', 'artifact', 'MFTJ')  # 상대 경로로 설정
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    run_MFTJ_parsing()
    

    
    # 2. 파싱한 MFT와 유저저널 분석 (csv & XML 생성)
    # 디렉토리 존재 여부 검증 로직
    csv_output_dir = os.path.join('..', '..', 'output', 'suspicious_artifact', 'MFTJ')  # CSV 파일 경로
    if not os.path.exists(csv_output_dir):
        os.makedirs(csv_output_dir)
    
    # 디렉토리 존재 여부 검증 로직
    xml_output_dir = os.path.join('..', '..', 'output', 'suspicious_artifact', 'MFTJ')  # xml 파일 경로
    if not os.path.exists(xml_output_dir):
        os.makedirs(xml_output_dir)
     
    run_MFTJ_sus_analysis()
    

if __name__ == "__main__":
    main()