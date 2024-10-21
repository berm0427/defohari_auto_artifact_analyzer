import os
import pandas as pd
import sys

def normalize_path(path):
    """
    중복된 경로나 불필요한 경로 요소를 정리하는 함수.
    """
    # os.path.normpath를 사용해 경로 중복을 해결하고 정규화함
    return os.path.normpath(path)

def upload_to_google_sheets(csv_file_path, json_credentials_path):
    """
    Uploads a CSV file to Google Sheets and returns the sheet ID.
    """
    # 경로 중복 처리
    csv_file_path = normalize_path(csv_file_path)

    if not os.path.exists(csv_file_path):
        print(f"File not found: {csv_file_path}")
        sys.exit(1)  # 파일을 찾을 수 없을 경우 스크립트를 중지하고 오류 코드 반환
    
    try:
        # CSV 파일을 읽어서 Google Sheets에 업로드하는 로직
        df = pd.read_csv(csv_file_path)
        print(f"CSV 파일이 성공적으로 로드되었습니다: {csv_file_path}")
        # 업로드 로직 구현...
        return "sheet_id_placeholder"  # 실제 Google Sheets API로부터 얻은 ID 반환
    except Exception as e:
        print(f"Error occurred while reading the CSV file: {csv_file_path}: {e}")
        sys.exit(1)

def main():
    # 경로 인자로 받기
    if len(sys.argv) != 3:
        print("Usage: python if_csv_broken_main.py <folder_name> <csv_file_path>")
        sys.exit(1)

    folder_name = sys.argv[1]
    csv_file_path = sys.argv[2]
    
    # 경로 정규화 (중복 처리)
    csv_file_path = normalize_path(csv_file_path)
    
    # 경로 유효성 체크
    if not os.path.exists(csv_file_path):
        print(f"Invalid CSV file path: {csv_file_path}")
        sys.exit(1)
    
    # Google Sheets 업로드 및 기타 로직
    json_credentials_path = 'your_google_credentials.json'
    sheet_id = upload_to_google_sheets(csv_file_path, json_credentials_path)
    
    # 시트 ID 출력 (또는 다른 후속 작업)
    print(f"Uploaded sheet ID: {sheet_id}")

if __name__ == "__main__":
    main()
