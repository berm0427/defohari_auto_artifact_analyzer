@echo off
chcp 65001 > nul
setlocal

REM 현재 디렉토리 확인
set "SOURCE=.."
set "DEST=..\.."

REM 각 폴더 이동
move "%SOURCE%\image_here" "%DEST%\image_here"
move "%SOURCE%\sleuthkit" "%DEST%\sleuthkit"
move "%SOURCE%\subroutine" "%DEST%\subroutine"
move "%SOURCE%\csv_totaler.py" "%DEST%\csv_totaler.py"
move "%SOURCE%\if_csv_broken_main.py" "%DEST%\if_csv_broken_main.py"

echo 폴더 이동 완료!
endlocal
pause
