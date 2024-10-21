import os
import pandas as pd
import subprocess

# 서브루틴에서 추출된 CSV 파일들의 경로를 지정
SUBROUTINE_PATHS = {
    "web": r"output\artifact\web\web_output.csv",              # web 분석 결과 경로
    "web_sus": r"output\suspicious_artifact\web\web_sus.csv",
    "mft": r"output\artifact\MFTJ\mft_output.csv",             # MFT 분석 결과 경로
    "mft_sus": r"output\suspicious_artifact\MFTJ\mft_filtered.csv",
    "usn": r"output\artifact\MFTJ\usn_output.csv",             # USN 분석 결과 경로
    "usn_sus": r"output\suspicious_artifact\MFTJ\usn_filtered.csv",
    "lnk": r"output\artifact\LNK\lnk_files_ccno.csv",    # LNK 분석 결과 경로
    "lnk_sus": r"output\suspicious_artifact\LNK\suspicious_antiforensic_lnk_files_ccno.csv",
    "evt_log": r"output\artifact\event_log\event_logs.csv",     # 이벤트 로그 분석 결과 경로
    "evt_sus": r"output\suspicious_artifact\event_log\anti_forensic_events.csv"
}

# Set of CSV files that may be broken
broken_file_name = {'web', 'lnk', 'evt_log'}

# Modify if_csv_broken to take the file path and folder name as arguments
def if_csv_broken(folder_name, file_path):
    try:
        # subprocess에서 경로 문제 방지
        result = subprocess.run(['python', 'if_csv_broken_main.py', folder_name, file_path], check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while running if_csv_broken for {file_path}: {e}")
        return False

# 각 서브루틴에서 추출한 CSV 파일을 수정하고 덮어쓰는 함수
def modify_and_save_csv(file_path):
    # 경로 중복 문제 해결: 파일 경로가 올바른지 확인
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return None

    folder_name = os.path.basename(os.path.dirname(file_path))

    # 파일 수정 프로세스 실행
    if folder_name in broken_file_name:
        success = if_csv_broken(folder_name, file_path)
        if not success:
            return None
    
    try:
        # 데이터 프레임을 low_memory=False로 읽기
        df = pd.read_csv(file_path, low_memory=False)
        df.fillna('')  # 필요 시 데이터 수정 작업 추가
        
        # 수정 후 파일을 덮어쓰기
        df.to_csv(file_path, index=False)
        print(f"File successfully saved: {file_path}")
        return file_path
    except Exception as e:
        print(f"Error occurred while reading or writing CSV file {file_path}: {e}")
        return None

# 각 서브루틴에서 추출한 CSV 파일을 수정하고 데이터를 읽는 함수
def load_and_modify_data(paths):
    data_frames = {}
    for folder_name, file_path in paths.items():
        # 경로 중복을 방지하여 정확한 경로만 처리
        if file_path.endswith(".csv") and os.path.exists(file_path):
            modified_file_path = modify_and_save_csv(file_path)
            if modified_file_path:
                try:
                    file_name = os.path.basename(modified_file_path).replace(".csv", "")
                    # 수정된 CSV 파일을 다시 읽어서 데이터프레임에 저장
                    data_frames[file_name] = pd.read_csv(modified_file_path, low_memory=False)
                except Exception as e:
                    print(f"Error occurred while reading modified CSV file {modified_file_path}: {e}")
        else:
            print(f"File not found or invalid: {file_path}")
    return data_frames

# 전체 데이터와 의심스러운 파일을 하나의 엑셀 파일에 저장하는 함수
def save_to_excel(data_frames, output_path="combined_analysis.xlsx"):
    with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
        for key, df in data_frames.items():
            sheet_name = key[:31].capitalize()
            df.to_excel(writer, sheet_name=sheet_name, index=False)
        print(f"Data exported to {output_path}")


# 메인 루틴 함수
def main_routine():
    print("Job is working. Please wait...")

    # 서브루틴에서 CSV 파일들 수정 후 로드
    data_frames = load_and_modify_data(SUBROUTINE_PATHS)

    # 전체 데이터를 통합하여 엑셀 파일로 출력
    save_to_excel(data_frames)

if __name__ == "__main__":
    main_routine()
