import os
import pandas as pd
import subprocess
import json
import sys

# 중복 제거 함수
def deduplicate_sus_files(sus_df):
    """
    Suspected (suspicious) CSV 파일에서 중복된 항목을 제거합니다.
    중복 기준은 'Executable'과 'Path'입니다.
    """
    deduplicated_df = sus_df.drop_duplicates(subset=['Executable', 'Path'])
    return deduplicated_df

# CSV 파일을 읽고, 수정하고, 중복을 제거하는 함수
def load_and_modify_data(selected_artifacts, paths):
    data_frames = {}
    for key, file_info in paths.items():
        if key not in selected_artifacts:
            continue  # 선택되지 않은 아티팩트는 건너뜀
        file_path = file_info['path']
        folder_name = file_info['folder']

        # CSV 파일 존재 여부 확인
        if file_path.endswith(".csv") and os.path.exists(file_path):
            try:
                # 데이터 프레임을 읽기
                df = pd.read_csv(file_path, low_memory=False)
                df.fillna('', inplace=True)  # 결측값을 빈 문자열로 처리
                file_name = os.path.basename(file_path).replace(".csv", "")

                # 의심스러운 파일은 중복 제거 후 처리
                if 'sus' in file_name:
                    df = deduplicate_sus_files(df)

                data_frames[file_name] = df

            except Exception as e:
                print(f"Error occurred while reading CSV file {file_path}: {e}")
        else:
            print(f"File not found or invalid: {file_path}")
    
    return data_frames

# 통합된 데이터를 엑셀 파일로 저장하는 함수
def save_to_excel(data_frames, output_path="combined_analysis.xlsx"):
    with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
        for key, df in data_frames.items():
            sheet_name = key[:31].capitalize()
            df.to_excel(writer, sheet_name=sheet_name, index=False)
        print(f"Data exported to {output_path}")

# 메인 루틴 함수
def main_routine(selected_artifacts):
    print("Job is working. Please wait...")

    # 서브루틴에서 추출된 CSV 파일들의 경로를 지정
    SUBROUTINE_PATHS = {
        "web": {
            "path": r"output\artifact\web\web_output.csv",
            "folder": "web"
        },
        "web_sus": {
            "path": r"output\suspicious_artifact\web\web_sus.csv",
            "folder": "web"
        },
        "mft": {
            "path": r"output\artifact\MFTJ\mft_output.csv",
            "folder": "MFTJ"
        },
        "mft_sus": {
            "path": r"output\suspicious_artifact\MFTJ\mft_filtered.csv",
            "folder": "MFTJ"
        },
        "usn": {
            "path": r"output\artifact\MFTJ\usn_output.csv",
            "folder": "MFTJ"
        },
        "usn_sus": {
            "path": r"output\suspicious_artifact\MFTJ\usn_filtered.csv",
            "folder": "MFTJ"
        },
        "lnk": {
            "path": r"output\artifact\LNK\lnk_files_ccno.csv",
            "folder": "LNK"
        },
        "lnk_sus": {
            "path": r"output\suspicious_artifact\LNK\suspicious_antiforensic_lnk_files_ccno.csv",
            "folder": "LNK"
        },
        "prefetch":{
           "path": r"output\artifact\prefetch\prefetch.csv",
           "folder": "prefetch"
        },
        "prefetch_sus":{
           "path": r"output\suspicious_artifact\prefetch\prefetch_sus.csv",
           "folder": "prefetch"
        }, 
        "evt_log": {
            "path": r"output\artifact\event_log\event_logs.csv",
            "folder": "event_log"
        },
        "evt_log_sus": {
            "path": r"output\suspicious_artifact\event_log\anti_forensic_events.csv",
            "folder": "event_log"
        }
    }

    # 선택된 아티팩트의 CSV 파일들 수정 후 로드
    data_frames = load_and_modify_data(selected_artifacts, SUBROUTINE_PATHS)

    if data_frames:
        # 전체 데이터를 통합하여 엑셀 파일로 출력
        save_to_excel(data_frames)
    else:
        print("선택된 아티팩트에 대한 CSV 파일이 없습니다.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        selected_artifacts_json = sys.argv[1]
        selected_artifacts = json.loads(selected_artifacts_json)
        main_routine(selected_artifacts)
    else:
        print("선택된 아티팩트 정보가 제공되지 않았습니다.")
