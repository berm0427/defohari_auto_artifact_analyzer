import os
import subprocess
import re

# Function to get partition offset
def get_partition_offset(image_path, partition_type="Basic data partition"):
    """Uses mmls to get the offset of the specified partition type."""
    try:
        command = ['mmls', image_path]
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        
        lines = result.stdout.splitlines()
        for line in lines:
            if partition_type in line:
                parts = line.split()
                if len(parts) > 2:
                    offset = parts[2]
                    print(f"partition offset: {offset}")
                    return int(offset)
    except subprocess.CalledProcessError as e:
        print(f"partition offset 못 찾음: {e}")
    return None

# Function to get inode number
def get_inode_number(image_path, offset, file_name, inode=None):
    """Uses fls to get the inode number of a file or directory."""
    try:
        if inode:
            command = ['fls', '-f', 'ntfs', '-o', str(offset), image_path, inode]
        else:
            command = ['fls', '-f', 'ntfs', '-o', str(offset), image_path]
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        
        for line in result.stdout.splitlines():
            if file_name in line:
                inode_number = line.split()[1].split(':')[0]
                return inode_number
    except subprocess.CalledProcessError as e:
        print(f"Error finding inode number: {e}")
    return None

# Function to extract .evtx files
def extract_evt_files(image_path, offset, output_dir):
    """Extracts specified .evtx files from the image."""
    # Get inodes of directories to navigate to Logs directory
    windows_inode = get_inode_number(image_path, offset, "Windows")
    if windows_inode is None:
        print("Windows directory 못 찾음.")
        return
    print(f"Windows inode: {windows_inode}")

    system32_inode = get_inode_number(image_path, offset, "System32", windows_inode)
    if system32_inode is None:
        print("System32 directory 못 찾음.")
        return
    print(f"System32 inode: {system32_inode}")

    winevt_inode = get_inode_number(image_path, offset, "winevt", system32_inode)
    if winevt_inode is None:
        print("winevt directory 못 찾음.")
        return
    print(f"winevt inode: {winevt_inode}")

    logs_inode = get_inode_number(image_path, offset, "Logs", winevt_inode)
    if logs_inode is None:
        print("Logs directory 못 찾음.")
        return
    print(f"Logs inode: {logs_inode}")

    # Get list of files in Logs directory
    try:
        evtx_files_output = subprocess.run(
            ['fls', '-f', 'ntfs', '-o', str(offset), image_path, logs_inode],
            capture_output=True, text=True, check=True
        ).stdout.splitlines()
    except subprocess.CalledProcessError as e:
        print(f"로그 디렉토리 파일 리스트 생성 중 오류 발생: {e}")
        return

    # Patterns to match the filenames we're interested in
    patterns = [
        r'^Microsoft-Windows-Windows Defender%4\w+\.evtx$',  # Defender event logs
        r'^Microsoft-Windows-Windows Firewall With Advanced Security%4\w+\.evtx$'  # Firewall event logs
    ]

    # Compile regex patterns
    compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in patterns]

    for line in evtx_files_output:
        if '.evtx' in line.lower():
            # Extract inode and filename
            parts = line.split()
            evtx_inode = parts[1].split(":")[0]
            evtx_filename = " ".join(parts[2:])

            # Check if filename matches any of the patterns
            for pattern in compiled_patterns:
                if pattern.match(evtx_filename):
                    evtx_output_path = os.path.join(output_dir, evtx_filename)
                    try:
                        # Extract the file using icat
                        command = ['icat', '-f', 'ntfs', '-o', str(offset), image_path, evtx_inode]
                        with open(evtx_output_path, 'wb') as f:
                            subprocess.run(command, stdout=f, check=True)
                        print(f"{evtx_filename} 를 {evtx_output_path}로 추출함")
                    except subprocess.CalledProcessError as e:
                        print(f"{evtx_filename} 추출 중 오류 발생: {e}")
                    break  # Stop checking patterns once matched

# Function to get the first disk image path
def get_first_disk_image_path(image_directory):
    # Disk image file extensions
    disk_image_extensions = ['.e01']
    
    # Search for files with disk image extensions
    for filename in os.listdir(image_directory):
        if any(filename.lower().endswith(ext) for ext in disk_image_extensions):
            return os.path.join(image_directory, filename)

    return None

# Main execution logic
if __name__ == "__main__":
    # Image file path and output directory
    image_path_directory = r"..\..\image_here"
    first_disk_image_path = get_first_disk_image_path(image_path_directory)
    if first_disk_image_path is None:
        print("No disk image file found.")
        exit(1)
    output_dir = r"..\..\output\artifact\defender_log"
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Get partition offset
    partition_offset = get_partition_offset(first_disk_image_path)
    if partition_offset is None:
        print("Partition offset 를 찾을 수 없음.")
        exit(1)
    
    # Extract evt files
    extract_evt_files(first_disk_image_path, partition_offset, output_dir)
