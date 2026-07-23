@echo off
REM ================================================================
REM  Che do NOI CHUYEN bang giong noi (khong co orb).
REM  TTS chay trong tien trinh (viXTTS) -> KHONG can server TTS.
REM  Muon co orb: dung Luna_Jarvis.bat
REM ================================================================
cd /d "%~dp0"

REM LUU Y: khong dung dau ">" trong lenh echo ??? CMD hieu la ghi ra file!
echo Khoi dong Luna: nghe mic, tra loi bang giong noi...
echo.
call .venv\Scripts\activate.bat
python scripts\voice_luna.py

echo.
pause >nul
