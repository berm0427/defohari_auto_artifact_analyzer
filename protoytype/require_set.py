import os
import subprocess
import pkg_resources
from concurrent.futures import ThreadPoolExecutor, as_completed
import importlib.util

# 모듈-패키지 매핑
PACKAGE_MAPPING = {
    'win32com': 'pywin32',
    'win32api': 'pywin32',
    'win32evtlog': 'pywin32',
    'win32evtlogutil': 'pywin32',
    'pythoncom': 'pywin32',
    'pytsk3': 'pytsk3',
    'openpyxl': 'openpyxl',
    'PIL': 'pillow'
}

def extract_imports_from_file(file_path):
    """파일에서 import된 패키지를 추출합니다."""
    imports = set()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        with open(file_path, 'r', encoding='latin-1') as f:
            lines = f.readlines()

    for line in lines:
        if line.startswith('import ') or line.startswith('from '):
            parts = line.split()
            if parts[0] == 'import':
                imports.add(parts[1].split('.')[0])
            elif parts[0] == 'from':
                imports.add(parts[1].split('.')[0])

    return imports

def find_requirements(directory):
    """디렉토리에서 파이썬 파일들을 병렬로 처리하여 import된 패키지를 찾습니다."""
    requirements = set()
    with ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(extract_imports_from_file, os.path.join(root, file))
            for root, _, files in os.walk(directory) for file in files if file.endswith('.py')
        ]
        for future in as_completed(futures):
            requirements.update(future.result())

    # 모듈 이름을 설치 가능한 패키지 이름으로 변환
    resolved_requirements = set(
        PACKAGE_MAPPING.get(pkg, pkg) for pkg in requirements
    )
    
    return resolved_requirements

def is_installable(package):
    """패키지가 pip로 설치 가능한지 확인합니다."""
    result = subprocess.run(
        ['pip', 'show', package],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    return result.returncode == 0

def filter_installable_packages(packages):
    """pip로 설치 가능한 패키지만 필터링합니다."""
    return {pkg for pkg in packages if is_installable(pkg)}

def main(directory):
    print(f"{directory}에서 파이썬 파일들을 스캔합니다...")

    # 필요한 패키지 탐색
    requirements = find_requirements(directory)
    print(f"발견된 패키지: {requirements}")

    # 설치 가능한 패키지 필터링
    installable_packages = filter_installable_packages(requirements)
    print(f"설치 가능한 패키지: {installable_packages}")

    # requirements.txt 생성
    with open('requirements2.txt', 'w', encoding='utf-8') as f:
        for package in sorted(installable_packages):
            f.write(f"{package}\n")

    print("requirements.txt 파일이 생성되었습니다.")

if __name__ == "__main__":
    # 스캔할 디렉토리 설정
    target_directory = "."  # 현재 디렉토리 또는 원하는 경로로 변경
    main(target_directory)
