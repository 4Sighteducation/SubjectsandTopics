@echo off
REM Test script for Eduqas GCSE Universal Scraper
REM Usage: TEST-EDUQAS-GCSE-UNIVERSAL.bat [subject_name]
REM Examples:
REM   TEST-EDUQAS-GCSE-UNIVERSAL.bat
REM   TEST-EDUQAS-GCSE-UNIVERSAL.bat "Geography A"
REM   TEST-EDUQAS-GCSE-UNIVERSAL.bat "Mathematics"

echo ========================================
echo Eduqas GCSE Universal Scraper - Test Run
echo ========================================
echo.

cd /d "%~dp0"

REM Check if subject name provided as argument
if "%~1"=="" (
    echo No subject specified - testing first 3 subjects
    echo.
    python eduqas-gcse-universal-scraper.py --limit 3
) else (
    echo Testing subject: %~1
    echo.
    python eduqas-gcse-universal-scraper.py --subject "%~1"
)

echo.
echo ========================================
echo Test complete!
echo Check reports folder for results
echo ========================================
pause

