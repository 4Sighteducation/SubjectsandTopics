@echo off
REM Quick check script to see which subjects had qualification selected correctly

echo Checking qualification selection in debug HTML files...
echo.

cd /d "%~dp0\debug-output"

for %%f in (ocr-gcse-*.html) do (
    echo Checking %%f...
    findstr /C:"pp-qual" /C:"selected" %%f | findstr /V "Which qualification" | findstr "selected"
    echo.
)

pause

