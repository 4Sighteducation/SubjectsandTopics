@echo off
REM Test Eduqas A-Level PDF URL Finder - Single Subject
REM Usage: TEST-ALEVEL-PDF-URL-SINGLE.bat "Subject Name"
REM Example: TEST-ALEVEL-PDF-URL-SINGLE.bat "Biology"

cd /d "%~dp0"

if "%~1"=="" (
    echo Usage: TEST-ALEVEL-PDF-URL-SINGLE.bat "Subject Name"
    echo.
    echo Available A-Level subjects:
    echo   Biology, Chemistry, Economics, Geography, Law, Physics, Psychology
    echo   English Language and Literature
    echo.
    echo Example: TEST-ALEVEL-PDF-URL-SINGLE.bat "Biology"
    pause
    exit /b 1
)

echo ========================================
echo Testing PDF URL Finder for A-Level
echo Subject: %~1
echo ========================================
echo.
echo This will:
echo 1. Navigate to Eduqas website
echo 2. Find the subject page for %~1 (A-Level)
echo 3. Extract the PDF URL
echo.
echo Browser will be visible so you can see what's happening...
echo.

python test-alevel-url-single.py "%~1"

pause

