메인 루틴 그리고 사브루틴에서는 LNK, web, event_log에는 구글 API (Google sheet, Google Drive) credential 파일이 필요합니다
<file_name>.json 형식의 파일을 생성한 후 이름을 반드시 'pycsvauto-df1c6762bab2'로 저장해주세요 (안 그러면 프로그램이 인식을 못합니다)

다른 이름을 하고 싶다면 if_csv_broken_<name>.py 이런 형식의 파일에서 직접 파일 경로를 수정해주셔야 하며, 이로 인해 발생하는 모든 오류는 본인 책임입니다

main routine, LNK, Web, event_log require Google API (Google Sheet, Google Drive) credential
You must create a file in the <file_name>.json format and save the name as 'pycsvauto-df1c6762bab2' (otherwise the program will not recognize it)

To specify another name, you must modify the file path directly from the file in the following format (if_csv_broken_<name>.py), and you are responsible for any errors