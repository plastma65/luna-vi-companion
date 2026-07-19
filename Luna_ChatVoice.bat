@echo off
REM ================================================================
REM  Che do: GO CHU de hoi, Luna tra loi bang GIONG NOI (+ orb).
REM  TTS chay trong tien trinh (piper) -> khong can server TTS.
REM ================================================================
cd /d "%~dp0"

echo Mo orb overlay...
start "" "%~dp0.venv\Scripts\pythonw.exe" "%~dp0scripts\overlay.py" --nodemo

REM LUU Y: khong dung dau ">" trong lenh echo — CMD hieu la ghi ra file!
echo Khoi dong Luna: go chu, Luna tra loi bang giong noi...
echo.
call .venv\Scripts\activate.bat
python scripts\chat_voice_luna.py

echo.
echo (Luna da dung. Tat orb neu con chay: bam dup Luna_Stop.vbs)
pause >nul
