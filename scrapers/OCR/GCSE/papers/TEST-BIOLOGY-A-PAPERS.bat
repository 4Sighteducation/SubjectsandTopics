@echo off
REM Test script for OCR GCSE Biology A (J247) past papers scraper - HEADLESS MODE

cd /d "%~dp0"

echo ========================================
echo OCR GCSE BIOLOGY A PAPERS SCRAPER TEST
echo ========================================
echo.
echo Running in HEADLESS mode (no browser window)
echo Subject: Biology A
echo Code: J247
echo.
echo This will scrape all past papers silently...
echo.

python scrape-ocr-gcse-papers-universal.py J247 "Biology A" "Biology A - J247 (from 2016)"

echo.
echo ========================================
echo Test complete!
echo ========================================
pause





















