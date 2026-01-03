@echo off
REM Test Eduqas A-Level Universal Scraper - Single Subject
REM Usage: TEST-EDUQAS-ALEVEL-SINGLE.bat "Subject Name"

cd /d "%~dp0"

if "%~1"=="" (
    echo Usage: TEST-EDUQAS-ALEVEL-SINGLE.bat "Subject Name"
    echo Example: TEST-EDUQAS-ALEVEL-SINGLE.bat "Biology"
    pause
    exit /b 1
)

echo ========================================
echo EDUQAS A-LEVEL UNIVERSAL SCRAPER - TEST
echo ========================================
echo.
echo Testing subject: %~1
echo.

python eduqas-alevel-universal-scraper.py --subject "%~1"

pause





















