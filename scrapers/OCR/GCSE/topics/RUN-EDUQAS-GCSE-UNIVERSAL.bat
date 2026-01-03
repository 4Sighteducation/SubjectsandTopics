@echo off
REM Full run script for Eduqas GCSE Universal Scraper
REM This will scrape all GCSE subjects

echo ========================================
echo Eduqas GCSE Universal Scraper - Full Run
echo ========================================
echo.
echo This will scrape all Eduqas GCSE qualifications.
echo This may take a while...
echo.

cd /d "%~dp0"

python eduqas-gcse-universal-scraper.py

echo.
echo ========================================
echo Scraping complete!
echo Check reports folder for results
echo ========================================
pause



