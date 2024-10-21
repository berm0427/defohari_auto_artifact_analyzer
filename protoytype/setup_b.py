from cx_Freeze import setup, Executable
import sys

# GUI 애플리케이션이므로 base 설정
base = None
if sys.platform == "win32":
    base = "Win32GUI"

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
        'subprocess',
    ],
    'excludes': [],
    'includes': [
        'tkinter',
        'tkinter.ttk',
        'tkinter.messagebox',
    ],
    'include_files': [
        ('subroutine/', 'subroutine/'),  # subroutine 폴더 포함
        ('csv_totaler.py', 'csv_totaler.py'),  # csv_totaler.py 파일 포함
        ('Depohari_Refined_Logo.png', 'Depohari_Refined_Logo.png'),  # GUI에 필요한 이미지 포함
    ],
    'include_msvcr': True,  # MS Visual C++ 재배포 가능 패키지 포함
    'silent': True,  # 콘솔 출력 숨기기
}

# 실행 파일 설정
executables = [
    Executable(
        script='defohari.py',
        base=base,
        target_name='ArtifactExtractor.exe',
        icon='Depohari_Refined_Logo.ico'  # 실행 파일 아이콘 설정
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
