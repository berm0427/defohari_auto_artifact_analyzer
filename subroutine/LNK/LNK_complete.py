# coding=UTF-8
import subprocess
import os

# 스크립트가 있는 디렉토리로 작업 디렉토리 변경
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

'''
def run_hive(image_path):
    """파싱한 하이브 파일을 저장"""
    hives_dir = os.path.join(os.getcwd(), r'..\web\extracted_hives')
    #script_path = r'..\web\web_hive_parsing_Log_num.py'
    if not os.path.exists(hives_dir):
        try:
            os.makedirs(hives_dir)
            print(f"'{hives_dir}' 폴더가 생성되었습니다.")
            subprocess.run(['python', r'..\web\web_hive_parsing_Log_num.py', '-o', r'subroutine\web\extracted_hives', image_path], check=True)
        except Exception as e:
            print(f"폴더 생성 중 오류 발생: {e}")
    else:
        print(f"'{hives_dir}' 폴더가 이미 존재합니다.")
        subprocess.run(['python', r'..\web\web_hive_parsing_Log_num.py', '-o', r'subroutine\web\extracted_hives', image_path], check=True)
'''

def run_LNK_parsing():
    """Step 1: lnk_parsing.py 실행, 파싱한 LNK파일을 저장"""
    subprocess.run(['python', 'lnk_parsing.py'], check=True)

def run_LNK_analysis():
    """Step 2: lnk1.py 실행, 리스트를 CSV와 xml 출력"""
    subprocess.run(['python', 'lnk1.py'], check=True)

def run_time_calibrator():
    """Step 2-1: 시간보정"""
    subprocess.run(['python', 'LnkTimeCalibrator.py'], check=True)
    
def run_merge_calibrator():
    """Step 2-2: 시간보정 결과 합치기"""
    subprocess.run(['python', 'merge_lnk_file.py'], check=True)

def run_LNK_sus_analysis():
    """Step 3: lnk pardon.py 실행 후 의심스러운 리스트를 CSV와 xml 출력"""
    subprocess.run(['python', 'lnk_pardon.py'], check=True)
    
def run_LNK_broken_recovery():
    """Step 4: 만일 csv가 깨졌다면 실행 (일반)"""
    subprocess.run(['python', 'if_csv_broken_lnk.py'], check=True)
    
def run_LNK_S_broken_recovery():
    """Step 4: 만일 csv가 깨졌다면 실행 (suspect)"""
    subprocess.run(['python', 'if_csv_broken_lnk_s.py'], check=True)


def main():
    # 1. lnk_parsing.py 실행, LNK 파싱
    output_dir = os.path.join('..', '..', 'output', 'artifact', 'LNK')  # 상대 경로로 설정
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    run_LNK_parsing()
    

    
    # 2. 파싱한 LNK분석 (csv & XML 생성)
    # 디렉토리 존재 여부 검증 로직
    csv_output_dir = os.path.join('..', '..', 'output', 'artifact', 'LNK')  # CSV 파일 경로 변경
    if not os.path.exists(csv_output_dir):
        os.makedirs(csv_output_dir)
        
    # 디렉토리 존재 여부 검증 로직
    xml_output_dir = os.path.join('..', '..', 'output', 'artifact', 'LNK')  # CSV 파일 경로 변경
    if not os.path.exists(csv_output_dir):
        os.makedirs(csv_output_dir)
     
    run_LNK_analysis()
    run_time_calibrator()
    run_merge_calibrator()
    run_LNK_broken_recovery()
    
    
    # 3. 의심가는 리스트 추출 (csv 생성)
    # 디렉토리 존재 여부 검증 로직
    csv_output_dir = os.path.join('..', '..', 'output', 'suspicious_artifact', 'LNK')  # CSV 파일 경로 변경
    if not os.path.exists(csv_output_dir):
        os.makedirs(csv_output_dir)
    
    run_LNK_sus_analysis()
    run_LNK_S_broken_recovery()
    

if __name__ == "__main__":
    # image_path = "F:\file_extract_torrent.E01"  # 분석할 이미지 파일 경로
    main()
