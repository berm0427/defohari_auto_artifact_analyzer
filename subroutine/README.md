메인 루틴 그리고 서브루틴에서는 LNK, web, event_log, defender_log(일부 구현이 안되어 있음)에는 

구글 API (Google sheet, Google Drive) credential 파일이 필요합니다

<file_name>.json 형식의 파일을 생성한 후 이름을 반드시 'pycsvauto-df1c6762bab2'로 저장해주세요 (안 그러면 프로그램이 인식을 못합니다)

다른 이름을 하고 싶다면 if_csv_broken_<name>.py 이런 형식의 파일에서 직접 파일 경로를 수정해주셔야 하며, 

이로 인해 발생하는 모든 오류는 본인 책임입니다

