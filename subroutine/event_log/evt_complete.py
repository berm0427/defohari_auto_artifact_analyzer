import subprocess
import os

# 스크립트가 있는 디렉토리로 작업 디렉토리 변경
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

def run_evt_parsing():
    """Step 1: evt_parsing.py 실행, 파싱한 LNK파일을 저장"""
    subprocess.run(['python', 'evt_parsing.py'], check=True)

def run_evt_analysis(App_path, Sys_path, Secu_path):
    """Step 2: evt.py 실행, 리스트를 CSV와 xml 출력"""
    subprocess.run(['python', 'evt.py', App_path, Sys_path, Secu_path], check=True)

def run_evt_sus_analysis():
    """Step 3: evt_sus.py 실행 후 의심스러운 리스트를 CSV와 xml 출력"""
    subprocess.run(['python', 'evt_sus.py'], check=True)

def run_evt_broken_recovery():
    """Step 4: 만일 csv가 깨졌다면 실행 (일반)"""
    subprocess.run(['python', 'if_csv_broken_log.py'], check=True)

def run_evt_S_broken_recovery():
    """Step 4: 만일 csv가 깨졌다면 실행 (suspect)"""
    subprocess.run(['python', 'if_csv_broken_log_s.py'], check=True)

def main():
    # 1. evt_parsing.py 실행, LNK 파싱
    output_dir = os.path.abspath(os.path.join('..', '..', 'output', 'artifact', 'event_log'))
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    run_evt_parsing()

    # 경로 설정: 절대 경로로 변환
    App_path = os.path.abspath(r'..\..\output\artifact\event_log\Application.evtx')
    Secu_path = os.path.abspath(r'..\..\output\artifact\event_log\Security.evtx')
    Sys_path = os.path.abspath(r'..\..\output\artifact\event_log\System.evtx')

    # 파일이 실제로 존재하는지 절대 경로로 검증
    print(f"App_path: {App_path}")
    print(f"Secu_path: {Secu_path}")
    print(f"Sys_path: {Sys_path}")

    if os.path.exists(App_path) and os.path.exists(Sys_path) and os.path.exists(Secu_path):
        run_evt_analysis(App_path, Sys_path, Secu_path)
        run_evt_broken_recovery()
    else:
        if not os.path.exists(App_path):
            print(f"{App_path} 파일이 존재하지 않습니다.")
        if not os.path.exists(Sys_path):
            print(f"{Sys_path} 파일이 존재하지 않습니다.")
        if not os.path.exists(Secu_path):
            print(f"{Secu_path} 파일이 존재하지 않습니다.")

    # 3. 의심가는 리스트 추출 (csv 생성)
    csv_output_dir = os.path.abspath(os.path.join('..', '..', 'output', 'suspicious_artifact', 'event_log'))
    if not os.path.exists(csv_output_dir):
        os.makedirs(csv_output_dir)

    run_evt_sus_analysis()
    run_evt_S_broken_recovery()

if __name__ == "__main__":
    main()