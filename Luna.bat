@echo off
REM Bấm đúp file này để trò chuyện với Luna (không cần nhớ lệnh).
cd /d "%~dp0"
call .venv\Scripts\activate.bat
python scripts\chat_luna_sft.py
echo.
echo (Luna da dung. Nhan phim bat ky de dong cua so.)
pause >nul
