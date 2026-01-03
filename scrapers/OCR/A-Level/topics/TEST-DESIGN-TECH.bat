@echo off
echo ================================
echo Testing OCR Design Technology Scraper
echo ================================
echo.
echo This scraper extracts 3 subjects from 1 PDF:
echo  - Design Engineering (H404)
echo  - Fashion and Textiles (H405)
echo  - Product Design (H406)
echo.
echo Each subject has 4 levels:
echo  - Level 0: Topic areas
echo  - Level 1: Main sections
echo  - Level 2: Numbered items
echo  - Level 3: Learning outcomes
echo.
pause

python ocr-design-tech-manual.py

echo.
echo ================================
echo Test complete!
echo Check data-viewer-v2.html to see results
echo ================================
pause

