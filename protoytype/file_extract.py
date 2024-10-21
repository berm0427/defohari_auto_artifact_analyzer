import pytsk3
import os
import sys
import subprocess


def mount_ewf_image(ewf_file, mount_point):
    """ewfmount를 사용하여 E01 이미지를 마운트하는 함수."""
    try:
        if not os.path.exists(mount_point):
            os.makedirs(mount_point)

        # ewfmount 명령어로 E01 파일 마운트
        subprocess.run(['ewfmount', ewf_file, mount_point], check=True)
        print(f"E01 이미지 {ewf_file} 마운트 완료: {mount_point}")
    except subprocess.CalledProcessError as e:
        print(f"E01 이미지 마운트 실패: {e}")
        sys.exit(1)


def unmount_ewf_image(mount_point):
    """마운트 해제 함수."""
    try:
        subprocess.run(['umount', mount_point], check=True)
        print(f"마운트 해제 완료: {mount_point}")
    except subprocess.CalledProcessError as e:
        print(f"마운트 해제 실패: {e}")


def extract_file(fs, file_entry, output_path):
    """특정 파일을 추출하여 출력 경로에 저장하는 함수."""
    try:
        with open(output_path, 'wb') as f_out:
            file_size = file_entry.info.meta.size
            if file_size is None:
                print(f"파일 크기가 유효하지 않음: {output_path}")
                return

            offset = 0
            size = 1024 * 1024  # 1MB씩 읽기

            while offset < file_size:
                available_to_read = min(size, file_size - offset)
                data = file_entry.read_random(offset, available_to_read)
                if not data:
                    break
                f_out.write(data)
                offset += available_to_read

        print(f"파일 추출 완료: {output_path}")
    except Exception as e:
        print(f"파일 추출 중 오류 발생: {e}")


def find_and_extract_files_by_extension(fs, directory, target_extension, output_dir):
    """디렉터리 내에서 특정 확장자를 가진 파일을 찾아서 추출하는 함수."""
    for entry in directory:
        if entry.info.name.name in [b'.', b'..']:  # .과 ..은 무시
            continue

        file_name = entry.info.name.name.decode()

        # 디렉터리일 경우 재귀적으로 탐색
        if entry.info.meta and entry.info.meta.type == pytsk3.TSK_FS_META_TYPE_DIR:
            sub_directory = entry.as_directory()
            new_output_dir = os.path.join(output_dir, file_name)  # 디렉터리 구조 유지
            if not os.path.exists(new_output_dir):
                os.makedirs(new_output_dir)  # 디렉터리 생성
            find_and_extract_files_by_extension(fs, sub_directory, target_extension, new_output_dir)

        # 파일이 target_extension과 일치하는 경우 추출
        elif file_name.endswith(target_extension):
            output_path = os.path.join(output_dir, file_name)
            if os.path.exists(output_path):
                print(f"파일이 이미 존재함: {output_path}. 건너뜀.")
                continue
            print(f"파일 찾음: {file_name}, 경로: {output_path}")
            extract_file(fs, entry, output_path)


def read_image_and_extract(image_path, target_extension, output_dir, mount_point):
    """이미지 파일에서 특정 확장자의 파일을 찾아서 추출하는 함수."""
    try:
        # 마운트된 경로에서 첫 번째 이미지 파일 사용
        img = pytsk3.Img_Info(f"{mount_point}/ewf1")
        fs = pytsk3.FS_Info(img)
        root_directory = fs.open_dir(path="/")

        # 파일 트리에서 확장자 기준으로 파일을 찾아서 추출
        find_and_extract_files_by_extension(fs, root_directory, target_extension, output_dir)
    except IOError as e:
        print(f"Error opening image: {e}")


if __name__ == "__main__":
    if len(sys.argv) != 5:
        print(f"Usage: {sys.argv[0]} <E01_image_file> <target_extension> <output_directory> <mount_point>")
        sys.exit(1)

    e01_image_file = sys.argv[1]
    target_extension = sys.argv[2]
    output_dir = sys.argv[3]
    mount_point = sys.argv[4]

    if not os.path.exists(e01_image_file):
        print(f"File {e01_image_file} does not exist.")
        sys.exit(1)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # E01 이미지 마운트
    mount_ewf_image(e01_image_file, mount_point)

    try:
        # 마운트된 이미지에서 파일 추출
        read_image_and_extract(e01_image_file, target_extension, output_dir, mount_point)
    finally:
        # 작업이 끝나면 마운트 해제
        unmount_ewf_image(mount_point)
