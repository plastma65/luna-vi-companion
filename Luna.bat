@echo off
REM Double-click this file to chat with Luna (type -> text reply).
cd /d "%~dp0"
call .venv\Scripts\activate.bat
echo.
echo   Dang nap Luna (lan dau import torch + model mat 30-60 giay, xin cho)...
echo   ^>^> DUNG bam Ctrl+C, cho toi khi thay dong "Luna san sang".
echo.
python scripts\chat_luna_sft.py
echo.
echo (Luna da dung. Nhan phim bat ky de dong cua so.)
pause >nul
