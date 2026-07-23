@echo off
REM ================================================================
REM  install.bat - TU DONG cai dat Luna tu dau den chay duoc.
REM
REM  Lam tuan tu: tao .venv -> cai PyTorch CUDA -> cai thu vien ->
REM  tai giong noi -> train tinh cach Luna. Xong la chay duoc.
REM
REM  File .exe (Luna_Setup.exe) se goi chinh file nay.
REM  Nguoi ranh tay co the bam dup truc tiep file nay cung duoc.
REM ================================================================
setlocal enabledelayedexpansion
cd /d "%~dp0"
chcp 65001 >nul
title Cai dat Luna

echo.
echo   ============================================================
echo         CAI DAT LUNA - Tro ly AI tieng Viet offline
echo   ============================================================
echo.
echo   Qua trinh nay tai ve khoang 10GB va mat 15-40 phut tuy mang.
echo   Yeu cau: GPU NVIDIA (khuyen nghi RTX 3060 12GB tro len).
echo.
pause

REM ---------- 1. Tim Python 3.11 ----------
echo.
echo   [1/6] Kiem tra Python 3.11...
set "PY="
py -3.11 --version >nul 2>&1 && set "PY=py -3.11"
if not defined PY (
    python --version 2>nul | findstr /c:"3.11" >nul && set "PY=python"
)
if not defined PY (
    echo.
    echo   [Loi] Khong tim thay Python 3.11.
    echo   Tai o: https://www.python.org/downloads/release/python-3119/
    echo   Khi cai, NHO tick o "Add Python to PATH".
    echo.
    pause
    exit /b 1
)
echo         OK: dung "%PY%"

REM ---------- 2. Tao moi truong ao ----------
echo.
echo   [2/6] Tao moi truong ao .venv...
if not exist ".venv\Scripts\activate.bat" (
    %PY% -m venv .venv
    if errorlevel 1 ( echo   [Loi] Tao venv that bai. & pause & exit /b 1 )
) else (
    echo         Da co san, bo qua.
)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip -q

REM ---------- 3. PyTorch ban CUDA ----------
echo.
echo   [3/6] Cai PyTorch (ban CUDA 12.1)... (nang, cho chut)
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
if errorlevel 1 ( echo   [Loi] Cai PyTorch that bai. & pause & exit /b 1 )

python -c "import torch;assert torch.cuda.is_available()" 2>nul
if errorlevel 1 (
    echo.
    echo   [Canh bao] GPU CUDA CHUA san sang. Luna se chay RAT cham tren CPU.
    echo   Neu may co GPU NVIDIA, kiem tra lai driver roi chay lai install.bat.
    echo.
    choice /c YN /m "   Van tiep tuc cai dat"
    if errorlevel 2 exit /b 1
) else (
    echo         OK: GPU da san sang.
)

REM ---------- 4. Thu vien con lai ----------
echo.
echo   [4/6] Cai cac thu vien con lai...
pip install -r requirements.txt
if errorlevel 1 ( echo   [Loi] Cai thu vien that bai. & pause & exit /b 1 )

REM ---------- 5. Tai giong noi viXTTS ----------
echo.
echo   [5/6] Tai giong noi viXTTS (~1.9GB)...
if exist "voices\viXTTS\config.json" (
    echo         Da co san, bo qua.
) else (
    python scripts\download_vixtts.py
    if errorlevel 1 ( echo   [Loi] Tai giong that bai. & pause & exit /b 1 )
)

REM ---------- 6. Train tinh cach Luna ----------
echo.
echo   [6/6] Huan luyen tinh cach Luna (tai model nen ~8GB + train)...
if exist "checkpoints\luna_lora\adapter_config.json" (
    echo         Da co san, bo qua.
) else (
    python scripts\train_luna_sft.py
    if errorlevel 1 ( echo   [Loi] Train that bai. & pause & exit /b 1 )
)

echo.
echo   ============================================================
echo         ??? CAI DAT XONG! Luna da san sang.
echo   ============================================================
echo.
echo   Cach chay:
echo     - Luna.vbs          : chay an, chi hien qua cau (orb)
echo     - Luna_Jarvis.bat   : noi chuyen bang giong + orb (co cua so)
echo     - Luna.bat          : go chu, Luna tra loi bang chu
echo.
echo   (Tuy chon) Cho Luna hoc an ninh mang - chay:
echo     python scripts\fetch_knowledge.py  roi  python scripts\build_index.py
echo.
pause
