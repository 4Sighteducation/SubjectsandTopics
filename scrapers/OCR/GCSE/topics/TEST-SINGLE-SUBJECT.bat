@echo off
REM Test script for testing a single Eduqas GCSE subject
REM Usage: TEST-SINGLE-SUBJECT.bat "Subject Name"
REM Examples:
REM   TEST-SINGLE-SUBJECT.bat "Geography A"
REM   TEST-SINGLE-SUBJECT.bat "Mathematics"
REM   TEST-SINGLE-SUBJECT.bat "English Literature"

echo ========================================
echo Eduqas GCSE Universal Scraper - Single Subject Test
echo ========================================
echo.

if "%~1"=="" (
    echo ERROR: No subject name provided!
    echo.
    echo Usage: TEST-SINGLE-SUBJECT.bat "Subject Name"
    echo.
    echo Examples:
    echo   TEST-SINGLE-SUBJECT.bat "Geography A"
    echo   TEST-SINGLE-SUBJECT.bat "Mathematics"
    echo   TEST-SINGLE-SUBJECT.bat "English Literature"
    echo.
    pause
    exit /b 1
)

cd /d "%~dp0"

echo Testing subject: %~1
echo.

python eduqas-gcse-universal-scraper.py --subject "%~1"

echo.
echo ========================================
echo Test complete!
echo Check reports folder for results
echo ========================================
pause



