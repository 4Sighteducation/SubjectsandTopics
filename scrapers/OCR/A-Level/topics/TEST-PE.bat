@echo off
echo ================================
echo Testing OCR Physical Education Scraper
echo ================================
echo.
echo This scraper creates ONE subject (H555) with 3 components:
echo  - Physiological factors affecting performance
echo  - Psychological factors affecting performance
echo  - Socio-cultural issues in physical activity and sport
echo.
echo Structure has 5 levels:
echo  - Level 0: Component name
echo  - Level 1: Main topics (e.g., 1.1.a, 1.2.a)
echo  - Level 2: Topic Area headings from tables
echo  - Level 3: Solid bullet points
echo  - Level 4: Open circle sub-bullets
echo.
echo NOTE: Asterisks (*) at start of topics are filtered out
echo       Icons in PDF are ignored
echo.
pause

python ocr-pe-manual.py

echo.
echo ================================
echo Test complete!
echo Check data-viewer-v2.html to see results
echo ================================
pause

