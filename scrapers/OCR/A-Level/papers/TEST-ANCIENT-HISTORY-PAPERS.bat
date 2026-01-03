@echo off
REM Test script for OCR Ancient History (H407) past papers scraper

cd /d "%~dp0"

echo ========================================
echo OCR ANCIENT HISTORY PAPERS SCRAPER TEST
echo ========================================
echo.
echo Using automatic mode with JavaScript dropdown selection
echo.

python scrape-ocr-papers-universal.py H407 "Ancient History" "Ancient History - H007, H407 (from 2017)" "A Level"

echo.
echo ========================================
echo Test complete!
echo ========================================
pause

