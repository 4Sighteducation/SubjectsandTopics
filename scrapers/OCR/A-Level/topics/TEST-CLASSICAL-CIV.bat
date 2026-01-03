@echo off
echo ================================
echo Testing OCR Classical Civilisation Scraper
echo ================================
echo.
echo This scraper extracts:
echo  - Level 0: Components
echo  - Level 1: Topics + Prescribed Books
echo  - Level 2: Key topics
echo  - Level 3: Learning outcomes
echo.
pause

python ocr-classical-civ-manual.py

echo.
echo ================================
echo Test complete!
echo Check data-viewer-v2.html to see results
echo ================================
pause

