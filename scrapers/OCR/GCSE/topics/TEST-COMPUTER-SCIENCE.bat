@echo off
REM Test script for Eduqas GCSE Universal Scraper - Computer Science only
REM This will test the Level 4+ extraction improvements

echo ========================================
echo Eduqas GCSE Universal Scraper - Test Run
echo Subject: Computer Science
echo ========================================
echo.
echo Testing Level 4+ extraction improvements...
echo.

cd /d "%~dp0"

python eduqas-gcse-universal-scraper.py --subject "Computer Science" --limit 1

echo.
echo ========================================
echo Test complete!
echo Check reports folder for Computer Science report
echo Look for Level 4+ topics in the levels section
echo ========================================
pause





















