@echo off
echo ================================
echo Testing OCR Chemistry B (Salters) Scraper
echo ================================
echo.
echo This uses the MANUAL STRUCTURE approach:
echo  Step 1: Manual Level 0 and Level 1 topics
echo  Step 2: PDF scrape for chemical ideas
echo.
pause

python ocr-chemistry-b-salters-manual.py

echo.
echo ================================
echo Test complete!
echo Check data-viewer-v2.html to see results
echo ================================
pause

