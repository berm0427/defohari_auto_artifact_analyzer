import sys
from Evtx.Evtx import Evtx  # 수정된 부분
import os

def evtx_to_xml(evtx_path, txt_path):
    with Evtx(evtx_path) as log:
        with open(txt_path, 'w', encoding='utf-8') as output_file:
            for record in log.records():
                try:
                    xml_data = record.xml()
                    output_file.write(xml_data + '\n\n')  # XML 데이터를 텍스트 파일에 저장
                except Exception as e:
                    print(f"Error parsing event: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python defender_log_parser.py <path_to_evtx_file>")
        sys.exit(1)

    evtx_file_path = sys.argv[1]
    xml_file_path = os.path.splitext(evtx_file_path)[0] + ".xml"  # 같은 이름의 .txt 파일 생성

    evtx_to_xml(evtx_file_path, xml_file_path)
    print(f"EVTX 파일이 {xml_file_path}로 변환되었습니다.")