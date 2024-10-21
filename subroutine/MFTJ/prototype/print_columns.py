import pandas as pd

def print_csv_columns(csv_file_path):
    try:
        df = pd.read_csv(csv_file_path, encoding='utf-8', low_memory=False, on_bad_lines='skip')
        print(f"'{csv_file_path}'의 열 이름:")
        print(df.columns.tolist())
    except FileNotFoundError:
        print(f"파일을 찾을 수 없습니다: {csv_file_path}")
    except Exception as e:
        print(f"파일 처리 중 오류가 발생했습니다: {e}")

if __name__ == "__main__":
    # MFT CSV 파일 경로
    mft_output_csv = r'..\..\output\artifact\MFTJ\mft_output.csv'
    # USN CSV 파일 경로
    usn_output_csv = r'..\..\output\artifact\MFTJ\usn_output.csv'

    print_csv_columns(mft_output_csv)
    print_csv_columns(usn_output_csv)
