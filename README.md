# defohari_auto_artifact_analyzer

Prefetch, LNK(JumpList), web log, evt_log, MFT & Usnjrnl을 디스크 이미지 덤프 단계에서 부터 추출하여 

자동 분석하는 도구입니다

안에 있는 requirement.txt를 참고하여 필수 요소들을 설치 후 사용하십시오 

※ 해당 도구는 오픈 소스 도구인 ※

※ sleuthkit, analyzeMFT, USN-Journal-Parser, python-evtx를 목적에 맞게 포팅하여 사용하였습니다 ※

setup.py를 이용하면 exe로 즐길 수 있습니다 --> python setup.py build를 cmd에 입력

현재 defender_log는 저희 목적에는 맞지 않아 도중 개발을 중단하여 

메인 루틴과(defohari.py)의 연계 및 소스코드 구현이 일부 안되어 있습니다

PythonCDR.py는 본 프로젝트와는 연관이 없지만 악성코드 무해화(CDR, Content Disarm&Reconstruction)를 MS word 기반에서 사용되도록 개발한 것입니다

이점 참고바랍니다
