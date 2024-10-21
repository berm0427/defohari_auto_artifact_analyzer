import xml.etree.ElementTree as ET
import csv
import sys
import os

# 네임스페이스 자동 감지 함수
def get_namespace(element):
    """ XML 요소에서 네임스페이스를 추출합니다. """
    match = element.tag.partition("}")[0] + "}"
    return match if match.startswith("{") else ""

def xml_to_csv(xml_file_path, output_csv_path):
    try:
        with open(xml_file_path, 'r', encoding='utf-8') as xml_file:
            event_data = ""
            event_count = 0
            with open(output_csv_path, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(["Program Name", "Log Time", "Log Content"])

                for line in xml_file:
                    line = line.strip()
                    event_data += line

                    # <Event> 태그가 끝나는 경우에만 처리
                    if line.startswith("</Event>"):
                        try:
                            root = ET.fromstring(event_data)  # 완전한 <Event> 태그 처리
                            event_count += 1

                            # 네임스페이스 추출
                            namespace = get_namespace(root)

                            # 프로그램 이름: Provider Name
                            provider = root.find(f".//{namespace}Provider")
                            if provider is not None:
                                program_name = provider.attrib.get("Name", "N/A")
                            else:
                                program_name = "N/A"

                            # 로그가 기록된 시간: TimeCreated의 SystemTime 속성
                            time_created = root.find(f".//{namespace}TimeCreated")
                            if time_created is not None:
                                log_time = time_created.attrib.get("SystemTime", "N/A")
                            else:
                                log_time = "N/A"

                            # 로그의 내용: EventData 내의 모든 데이터를 하나의 문자열로 합침
                            log_content = " | ".join(
                                [data.text for data in root.findall(f".//{namespace}Data") if data.text]
                            )

                            # CSV 파일에 행 추가
                            writer.writerow([program_name, log_time, log_content])
                        except ET.ParseError as e:
                            print(f"XML 파싱 중 오류 발생: {e}")
                        finally:
                            event_data = ""  # 초기화하여 다음 이벤트 처리

        print(f"{event_count}개의 이벤트가 {output_csv_path}로 변환되었습니다.")
    except Exception as e:
        print(f"오류 발생: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python defender_log_parser.py <path_to_xml_file>")
        sys.exit(1)

    xml_file_path = sys.argv[1]
    output_csv_path = os.path.splitext(xml_file_path)[0] + ".csv"  # 같은 이름의 .csv 파일 생성

    xml_to_csv(xml_file_path, output_csv_path)
