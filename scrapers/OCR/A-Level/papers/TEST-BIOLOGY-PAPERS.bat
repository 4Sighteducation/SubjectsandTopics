@echo off
REM Test script for OCR Biology A (H420) past papers scraper - HEADLESS MODE

cd /d "%~dp0"

echo ========================================
echo OCR BIOLOGY A PAPERS SCRAPER TEST
echo ========================================
echo.
echo Running in HEADLESS mode (no browser window)
echo Subject: Biology A
echo Code: H420
echo.
echo This will scrape all past papers silently...
echo.

python scrape-ocr-papers-universal.py H420 "Biology A" "Biology A - H020, H420 (from 2015)" "A Level"

echo.
echo ========================================
echo Test complete!
echo ========================================
pause





















