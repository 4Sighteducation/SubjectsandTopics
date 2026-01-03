@echo off
REM Test Eduqas A-Level Universal Scraper
REM Tests on 1-2 subjects to verify URL finding and extraction depth

cd /d "%~dp0"

echo ========================================
echo EDUQAS A-LEVEL UNIVERSAL SCRAPER - TEST
echo ========================================
echo.
echo Testing on 1-2 subjects...
echo.

python eduqas-alevel-universal-scraper.py --limit 2

pause





















