import pytz
import struct
import os
import sqlite3
from datetime import datetime, timedelta

# chrome, whale and Edge (New versions written based on chromium only) time parser
def parse_chrome_whale_EdgeN(history_file):
    conn = sqlite3.connect(history_file)
    c = conn.cursor()
    c.execute("SELECT url, last_visit_time FROM urls")
    rows = c.fetchall()
    conn.close()

    urls = []
    for row in rows:
        url = row[0]
        timestamp = row[1] / 1000000  # convert microsecond to second 
        visit_time = datetime(1601, 1, 1) + timedelta(seconds=timestamp)
        korea_timezone = pytz.timezone('Asia/Seoul')
        korea_time = visit_time.replace(tzinfo=pytz.utc).astimezone(korea_timezone)
        if timestamp == 0:
            continue # no blank
            # print("we didn't find visit_time this url: " + url) # with blank
        else:
            urls.append((url, korea_time))
    return urls

# edge browser reaing (legarcy) Under construction...
# def parse_edge(cache_file):
    urls = []

    with open(cache_file, 'rb') as f:
        # 매직 넘버 확인
        magic_number = f.read(4)
        if magic_number != b'\x16\x7A\x45\xCD':
            print("not Edge cache file")
            return urls

        # DB header reading
        f.seek(8)
        version = struct.unpack('<I', f.read(4))[0]

        # DB record reading
        while True:
            try:
                record_size = struct.unpack('<I', f.read(4))[0]
                if record_size == 0:
                    break

                # URL length reading
                url_length = struct.unpack('<I', f.read(4))[0]


                # URL reading
                url = f.read(url_length).decode('utf-8', errors='ignore')

                # visit_time reading (Chromium Time Microseconds type)
                visit_time_micros = struct.unpack('<Q', f.read(8))[0]
                visit_time_seconds = visit_time_micros / 1000000 - 11644473600
                timezone = pytz.timezone('Asia/Seoul')
                k_visit_time = datetime.fromtimestamp(visit_time_seconds, tz=timezone)

                urls.append((url, k_visit_time))

                # move to next record
                f.seek(record_size - (url_length + 16), 1)

            except Exception as e:
                print("Edge cache file parsing error:", e)
                break

    return urls

def parse_firefox_history(history_file):
    conn = sqlite3.connect(history_file)
    c = conn.cursor()
    c.execute("SELECT url, last_visit_date FROM moz_places")
    rows = c.fetchall()
    conn.close()

    urls = []
    for row in rows:
        url = row[0]
        if row[1] is None or row[1] == 0:
            continue # no blank

            ''' # with blank
            print("We didn't find visit time for this URL:", url) 
            continue  # 타임스탬프가 없거나 0이면 이후 처리를 스킵
            '''
        timestamp = row[1] / 1000000  # microseconds to seconds
        visit_time = datetime.fromtimestamp(timestamp, tz=pytz.utc)  # UTC 기준으로 datetime 객체 생성
        korea_time = pytz.timezone('Asia/Seoul')
        korea_time = visit_time.astimezone(korea_time)  # UTC 객체를 한국 시간대로 변환
        if timestamp == 0:
            continue # no blank
            # print("we didn't find visit_time this url: " + url) # with blank
        else:
            urls.append((url, korea_time))
    return urls

def generate_xml(urls):
    xml_output = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml_output += '<history>\n'
    for url, visit_time in urls:
        xml_output += f'  <visit>\n'
        xml_output += f'    <url>{url}</url>\n'
        xml_output += f'    <visit_time>{visit_time}</visit_time>\n'
        xml_output += f'  </visit>\n'
    xml_output += '</history>'
    return xml_output

def main():
    # chrome_history_file = 'History_chrome'
    # firefox_history_file = 'firefox_places.sqlite'
    # whale_history_file = 'History_whale' 
    edge_file = r'..\..\output\artifact\web\History_edge_ccno'   

    # chrome_urls = parse_chrome_whale_EdgeN(chrome_history_file)
    # whale_urls = parse_chrome_whale_EdgeN(whale_history_file)
    # firefox_urls = parse_firefox_history(firefox_history_file)
    edgeN_urls = parse_chrome_whale_EdgeN(edge_file)

    # all_urls = chrome_urls + whale_urls + edgeN_urls + firefox_urls
    all_urls = edgeN_urls
    all_urls.sort(key=lambda x: x[1], reverse=True)  # Backward order of time
    xml_output = generate_xml(all_urls)
    
    # 파일에 출력하는 부분
    output_file = r'..\..\output\artifact\web\web_output.xml'  # 저장할 파일 경로 및 이름
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(xml_output)
    print(f"XML output saved to {output_file}")

    # print(xml_output)

if __name__ == "__main__":
    main()
