@echo off
REM Full Eduqas A-Level Universal Scraper Batch Run
REM Processes all A-Level subjects

cd /d "%~dp0"

echo ========================================
echo EDUQAS A-LEVEL UNIVERSAL SCRAPER
echo ========================================
echo.
echo Processing ALL A-Level subjects...
echo This will take a while - please be patient...
echo.

python eduqas-alevel-universal-scraper.py

pause





















