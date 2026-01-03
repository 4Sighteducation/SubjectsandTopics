@echo off
echo ================================
echo Testing OCR Drama and Theatre Scraper
echo ================================
echo.
echo This scraper:
echo  - Component 3: Manual structure (themes + texts)
echo  - Component 4: Manual + scraped general content
echo.
pause

python ocr-drama-theatre-manual.py

echo.
echo ================================
echo Test complete!
echo Check data-viewer-v2.html to see results
echo ================================
pause

