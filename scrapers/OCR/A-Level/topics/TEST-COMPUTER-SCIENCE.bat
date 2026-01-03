@echo off
echo ================================
echo Testing OCR Computer Science Scraper
echo ================================
echo.
echo This scraper extracts 5 levels:
echo  - Level 0: Components
echo  - Level 1: Major sections (PDF's 1.1, 1.2)
echo  - Level 2: Subsection headers
echo  - Level 3: Specific topics (PDF's 1.1.1, 1.1.2)
echo  - Level 4: Learning outcomes (PDF's a, b, c)
echo.
pause

python ocr-computer-science-manual.py

echo.
echo ================================
echo Test complete!
echo Check data-viewer-v2.html to see results
echo ================================
pause

