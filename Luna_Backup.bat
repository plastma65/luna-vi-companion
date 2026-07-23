@echo off
cd /d "%~dp0"
echo Sao luu code Luna len GitHub...
echo (Ky uc rieng facts.json da bi .gitignore chan, khong len mang)
echo.
git add -A
git commit -m "Sao luu Luna"
git push
echo.
echo Xong. Nhan phim bat ky de dong.
pause >nul
