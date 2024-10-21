from Registry import Registry
from datetime import datetime, timedelta
import os

# 스크립트가 있는 디렉토리로 작업 디렉토리 변경
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)


def clean_username(candidate):
    """
    비정상적인 문자들을 제거하는 함수
    """
    return ''.join(c for c in candidate if c.isprintable()).rstrip('ȁ')

def map_friendly_name(username):
    """
    사용자 이름을 친숙한 계정 이름으로 매핑하는 함수.
    특정 이름이 아닌 경우 그대로 반환.
    """
    mappings = {
        "관리하도록 기본 제공된 계정": "Administrator",
        "게스트가 컴퓨터 도메인을 액세스하도록 기본 제공된 계정": "Guest",
        "defaultuser0": "Default User"
    }
    
    return mappings.get(username, username)  # 매핑된 이름이 없으면 그대로 반환

def filetime_to_dt(filetime):
    """Convert Windows FILETIME to a readable datetime format."""
    try:
        if filetime == 0:
            return None  # Zero filetime indicates no login
        dt = datetime(1601, 1, 1) + timedelta(microseconds=filetime / 10)
        if dt.year == 1601:
            return None  # Handle as "Never logged in"
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        print(f"filetime_to_dt error: {e}")
        return None
        
users = set()  # 저장용 set
def s_find_user(sam_hive_path):
    # 특정 RID로 Username을 찾고 싶을 때
    find_user = ""
    rid_to_find = "000003E9"  # 찾고 싶은 RID 값

    # users_data 리스트에서 RID를 검색하여 대응하는 Username 추출
    for user in users_data:
        if user['RID'] == rid_to_find:
            print(f"Username for RID {rid_to_find}: {user['Username']}")
            find_user = user['Username']
            break
    else:
        print(f"Username not found for RID {rid_to_find}")

    print(find_user) # 사용예제
    
def find_user_name():
    # Username 사용법 로직
    for user in users_data:
        print(user['Username'])


def get_user_info_from_sam(sam_hive_path):
    """
    SAM hive에서 RID와 Username, Last Logon 정보를 추출하는 함수
    """
    sam = Registry.Registry(sam_hive_path)

    # 사용자 정보가 있는 경로 (SAM\Domains\Account\Users)
    users_key = sam.open("SAM\\Domains\\Account\\Users")

    user_info = []
    
    # 각 RID에 해당하는 정보를 순회
    for rid_key in users_key.subkeys():
        rid = rid_key.name()  # 각 RID 값 (ex: 000001F4)

        # 'Names'와 같은 비-RID 키를 제외
        if rid == "Names":
            print(f"Skipping non-RID key: {rid}")  # 디버깅 출력
            continue

        print(f"Processing RID: {rid}")  # 디버깅 출력

        try:
            # 각 RID 하위의 V 값을 가져옴
            user_data = rid_key.value("V").value()
            print(f"Found 'V' value for RID: {rid}")  # 디버깅 출력

            # 여러 위치에서 사용자 이름을 찾기 위한 탐색
            username = None
            for possible_offset in range(0xC0, len(user_data), 2):
                try:
                    # UTF-16로 디코딩 시도 (종료 조건: \x00\x00 기준)
                    end = user_data.find(b'\x00\x00', possible_offset)
                    if end == -1:
                        end = possible_offset + 64  # 기본적으로 64바이트만 확인
                    
                    candidate = user_data[possible_offset:end].decode('utf-16le').rstrip('\x00')

                    # 유효한 사용자 이름으로 추정되는지 확인
                    if all(c.isprintable() or c.isspace() for c in candidate) and len(candidate) > 4:
                        # 비정상적인 문자 (예: 'ȁ')를 제거
                        candidate = clean_username(candidate)
                        username = map_friendly_name(candidate)  # 친숙한 이름으로 매핑
                        print(f"Found valid username at offset {possible_offset}: {username}")
                        break
                except UnicodeDecodeError:
                    continue
            
            # 이름을 찾지 못한 경우
            if not username:
                username = "<Unknown>"

            # Last Login Time을 F 값에서 추출
            last_logon_time = "Never logged in"
            try:
                f_value = rid_key.value("F").value()
                if len(f_value) >= 16:
                    filetime_value = int.from_bytes(f_value[8:16], byteorder='little')
                    last_logon_time = filetime_to_dt(filetime_value) or "Never logged in"
            except Exception as e:
                print(f"Failed to extract Last Logon for {username}: {e}")

        except KeyError:
            # 'V' 값이 없을 경우 처리
            username = "<V value not found>"
            print(f"No 'V' value for RID: {rid}")  # 디버깅 출력

        # 최종 출력 형식에 맞게 저장
        user_info.append({
            "RID": rid,
            "Username": username,
            "LastLogon": last_logon_time
        })
    
    return user_info

# SAM 하이브 파일 경로 지정
sam_hive_path = r"extracted_hives\SAM"

# SAM 하이브에서 사용자 정보 추출
users_data = get_user_info_from_sam(sam_hive_path)

# 저장용 set에 Username:RID LastLogon 형식으로 저장

for user in users_data:
    users.add(f"{user['Username']}:{user['RID']} {user['LastLogon']}")

# 각 사용자에 대해 정보 출력 (Username_RID LastLogon)
for user_entry in users:
    print(user_entry)