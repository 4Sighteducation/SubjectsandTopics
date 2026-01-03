@echo off
echo ================================
echo Testing OCR Ancient History Scraper
echo ================================
echo.
echo This uses the MANUAL STRUCTURE approach:
echo  Step 1: Manual Level 0 and Level 1 topics
echo  Step 2: PDF scrape for Level 2+ details
echo.
pause

python ocr-ancient-history-manual.py

echo.
echo ================================
echo Test complete!
echo Check data-viewer-v2.html to see results
echo ================================
pause

