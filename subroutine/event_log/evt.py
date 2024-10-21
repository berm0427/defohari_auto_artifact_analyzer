import win32evtlog
import win32evtlogutil
import sys
import csv
import xml.etree.ElementTree as ET
from xml.dom import minidom
import os
from datetime import datetime, timezone, timedelta
import pywintypes
import xml.sax.saxutils as saxutils

def clean_event_message(message):
    """
    이벤트 메시지에서 불필요한 줄바꿈 및 공백을 제거하고,
    깨진 문자나 특수 문자를 적절히 처리한다.
    """
    # UTF-8로 인코딩을 명시적으로 지정 (필요시 인코딩 처리)
    try:
        message = message.encode('utf-8').decode('utf-8', 'replace')
    except UnicodeEncodeError:
        message = "인코딩 오류가 발생한 메시지입니다."

    # 불필요한 줄바꿈과 공백을 제거하고 XML 특수 문자를 처리
    cleaned_message = saxutils.escape(message.strip())
    
    # 여러 줄로 나뉜 경우 하나로 병합
    cleaned_message = ' '.join(cleaned_message.splitlines())
    
    return cleaned_message

def read_event_logs(server, log_files):
    # log_files는 로그 종류와 파일 경로의 딕셔너리 {"Application": "path_to_app.evtx", ...}

    # CSV 파일 준비
    csv_file = open(r'..\..\output\artifact\event_log\event_logs.csv', 'w', newline='', encoding='utf-8')
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(['로그 종류', '시간', '이벤트 ID', '이벤트 내용'])
    
    # XML 파일 준비
    root = ET.Element('EventLogs')
    
    for log_type, file_path in log_files.items():
        if not os.path.exists(file_path):
            print(f"{file_path} 파일이 존재하지 않습니다. 건너뜁니다.")
            continue

        print(f"{log_type} 로그를 처리 중입니다...")
        try:
            # 백업된 이벤트 로그 파일 열기
            log_handle = win32evtlog.OpenBackupEventLog(server, file_path)
        except Exception as e:
            print(f"{file_path} 파일을 여는 중 오류 발생: {e}")
            continue
    
        flags = win32evtlog.EVENTLOG_FORWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
        total_records = win32evtlog.GetNumberOfEventLogRecords(log_handle)
    
        print(f"총 {total_records}개의 {log_type} 이벤트 로그가 있습니다.\n")
    
        events = True
        while events:
            events = win32evtlog.ReadEventLog(log_handle, flags, 0)
            for event in events:
                # 이벤트 발생 시간 가져오기
                event_time = event.TimeGenerated  # pywintypes.datetime 객체

                # 시간대 정보가 없으므로 UTC 시간대로 설정
                event_time = event_time.replace(tzinfo=timezone.utc)

                # 한국 시간대(KST)로 변환
                kst_timezone = timezone(timedelta(hours=9))
                event_time_kst = event_time.astimezone(kst_timezone)

                # 시간을 문자열로 포맷팅
                time_generated = event_time_kst.strftime('%Y-%m-%d %H:%M:%S')

                event_id = event.EventID & 0xFFFF  # 이벤트 ID

                # 이벤트 메시지 내용 가져오기
                try:
                    event_message = win32evtlogutil.SafeFormatMessage(event, log_type)
                    # 메시지를 정리하고, 깨진 문자 처리
                    event_message = clean_event_message(event_message)
                except Exception as e:
                    event_message = f"메시지를 가져오는 중 오류 발생: {e}"

                # 이벤트 내용이 비어있으면 로그에서 제외
                if not event_message.strip():
                    continue  # 비어있는 내용의 이벤트는 제외

                # CSV 파일에 쓰기
                csv_writer.writerow([log_type, time_generated, event_id, event_message])

                # XML 파일에 쓰기
                event_element = ET.SubElement(root, 'Event')
                ET.SubElement(event_element, '로그종류').text = log_type
                ET.SubElement(event_element, '시간').text = time_generated
                ET.SubElement(event_element, '이벤트ID').text = str(event_id)
                ET.SubElement(event_element, '이벤트내용').text = event_message

        win32evtlog.CloseEventLog(log_handle)
    
    # XML 문자열로 변환하고 들여쓰기 적용
    xml_str = ET.tostring(root, encoding='utf-8')
    parsed_xml = minidom.parseString(xml_str)
    pretty_xml_str = parsed_xml.toprettyxml(indent="  ")
    
    # XML 파일 저장
    with open(r'..\..\output\artifact\event_log\event_logs.xml', 'w', encoding='utf-8') as xml_file:
        xml_file.write(pretty_xml_str)
    
    csv_file.close()

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(f"사용법: {sys.argv[0]} <Application.evtx 경로> <System.evtx 경로> <Security.evtx 경로>")
        sys.exit(1)
    
    # 명령행 인자로부터 파일 경로 받기
    application_log_path = sys.argv[1]
    system_log_path = sys.argv[2]
    security_log_path = sys.argv[3]
    
    # 로그 종류와 파일 경로를 딕셔너리로 구성
    log_files = {
        "Application": application_log_path,
        "System": system_log_path,
        "Security": security_log_path
    }
    
    # 로컬 서버의 이벤트 로그 읽기
    read_event_logs(None, log_files)
