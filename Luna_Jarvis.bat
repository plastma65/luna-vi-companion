@echo off
REM ================================================================
REM  LUNA JARVIS (ban co cua so de xem log/debug): orb + giong noi.
REM  TTS chay trong tien trinh (piper) -> khong can server TTS.
REM ================================================================
cd /d "%~dp0"

echo Mo orb overlay...
start "" "%~dp0.venv\Scripts\pythonw.exe" "%~dp0scripts\overlay.py" --nodemo

echo Khoi dong Luna (giong noi + orb)...
echo.
call .venv\Scripts\activate.bat
python scripts\voice_luna.py

echo.
echo (Luna da dung. Tat orb neu con chay: bam dup Luna_Stop.vbs)
pause >nul
