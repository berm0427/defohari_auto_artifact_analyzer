from cx_Freeze import setup, Executable
import sys
import os
import shutil

# GUI 애플리케이션이므로 base 설정
base = None
if sys.platform == "win32":
    base = "Win32GUI"

'''
def ensure_directory_exists(directory):
    """디렉토리가 존재하지 않으면 생성합니다."""
    if not os.path.exists(directory):
        os.makedirs(directory)
'''

def find_json_files():
    """현재 디렉토리와 하위 디렉토리의 모든 JSON 파일을 찾습니다."""
    json_files = []
    for root, _, files in os.walk('.'):
        for file in files:
            if file.endswith('.json'):
                full_path = os.path.join(root, file)
                json_files.append((full_path, full_path))  # (원본 경로, 대상 경로)
    return json_files

'''
def find_build_folder():
    """빌드 폴더를 동적으로 찾습니다."""
    for root, dirs, _ in os.walk("build"):
        for d in dirs:
            if d.startswith("exe"):
                return os.path.join(root, d)  # 동적으로 빌드 폴더 반환
    raise FileNotFoundError("빌드 폴더를 찾을 수 없습니다.")
'''

# 빌드 옵션 설정
build_exe_options = {
    'packages': [
        'tkinter',
        'threading',
        'queue',
        'json',
        'concurrent.futures',
        'time',
        'os',
        'sys',
        'subprocess'
    ],
    'excludes': [],
    'includes': [
        'tkinter',
        'tkinter.ttk',
        'tkinter.messagebox',
    ],
    'include_files': ([  
        ('subroutine/', 'subroutine/'),  
        ('image_here/', 'image_here/'),  
        ('csv_totaler.py', 'csv_totaler.py'),  
        ('computer_monitor_icon.ico', 'computer_monitor_icon.ico'),  
        ('Depohari_Refined_Logo.png', 'Depohari_Refined_Logo.png'),  
        ('if_csv_broken_main.py', 'if_csv_broken_main.py'),  
        ('sleuthkit/', 'sleuthkit/')
    ] + find_json_files()),
    'include_msvcr': True,
    'silent': True,
}

# 실행 파일 설정
executables = [
    Executable(
        script='defohari.py',
        base=base,
        target_name='ArtifactExtractor.exe',
        icon='computer_monitor_icon.ico'
    )
]

# setup 함수 호출
setup(
    name='ArtifactExtractor',
    version='1.0',
    description='Defohari Artifact Extractor',
    options={'build_exe': build_exe_options},
    executables=executables
)
