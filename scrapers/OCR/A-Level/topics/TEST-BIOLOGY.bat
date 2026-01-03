@echo off
echo ================================
echo Testing OCR Biology A Scraper
echo ================================
echo.
echo This will test the two-stage scraper:
echo  Stage 1: HTML "at a glance" for structure
echo  Stage 2: PDF for detailed sub-topics
echo.
pause

python ocr-alevel-smart-scraper.py AL-BiologyA

echo.
echo ================================
echo Test complete!
echo Check data-viewer-v2.html to see results
echo ================================
pause

