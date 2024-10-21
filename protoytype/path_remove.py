import os
import sys
import winreg as reg
import ctypes

def is_admin():
    """Check if the user has admin privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def remove_from_path(relative_path):
    # 현재 스크립트가 위치한 디렉토리 경로 얻기
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 상대 경로를 기반으로 제거할 경로 생성
    target_path = os.path.join(current_dir, relative_path)

    # 현재 PATH 환경 변수 가져오기
    original_path = os.environ.get('PATH', '')
    
    # 제거할 경로가 존재하는지 확인
    if target_path in original_path:
        # 경로 제거
        new_path = original_path.replace(f";{target_path}", "").replace(target_path + ";", "").replace(target_path, "")
        
        # 시스템 PATH에 변경 사항 적용하기 위해 레지스트리 수정
        try:
            reg_key = reg.OpenKey(reg.HKEY_LOCAL_MACHINE, r'SYSTEM\CurrentControlSet\Control\Session Manager\Environment', 0, reg.KEY_SET_VALUE)
            reg.SetValueEx(reg_key, 'Path', 0, reg.REG_EXPAND_SZ, new_path)
            reg.CloseKey(reg_key)

            print(f"PATH에서 {target_path}가 영구적으로 제거되었습니다.")
        except Exception as e:
            print(f"PATH 제거 중 오류 발생: {e}")
    else:
        print(f"지정된 경로 {target_path}가 PATH에 존재하지 않습니다.")

if __name__ == "__main__":
    # 관리자 권한으로 실행 여부 확인
    if not is_admin():
        # 관리자 권한으로 재실행
        print("관리자 권한으로 재실행 중...")
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    else:
        # 'sleuthkit/bin' 경로를 제거
        remove_from_path(r'sleuthkit\bin')
