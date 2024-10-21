from Registry import Registry

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

def get_user_info_from_sam(sam_hive_path):
    """
    SAM hive에서 RID와 Username을 추출하는 함수
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

        except KeyError:
            # 'V' 값이 없을 경우 처리
            username = "<V value not found>"
            print(f"No 'V' value for RID: {rid}")  # 디버깅 출력

        user_info.append({
            "RID": rid,
            "Username": username
        })
    
    return user_info

# SAM 하이브 파일 경로 지정
sam_hive_path = r"extracted_hives\\SAM"

# SAM 하이브에서 사용자 정보 추출
users = get_user_info_from_sam(sam_hive_path)

# 각 사용자에 대해 정보 출력
for user in users:
    print(f"RID: {user['RID']}, Username: {user['Username']}")
