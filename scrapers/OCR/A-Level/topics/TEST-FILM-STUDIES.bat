@echo off
echo ================================
echo Testing OCR Film Studies Scraper
echo ================================
echo.
echo This scraper creates ONE subject (H410) with 2 components:
echo  - Component 01: Film History
echo  - Component 02: Critical Approaches to Film
echo.
echo Structure has 4 levels:
echo  - Level 0: Component name
echo  - Level 1: Film categories (Silent Era, Contemporary British, etc.)
echo  - Level 2: Topics from "Topic" column
echo  - Level 3: Learning outcome bullet points
echo.
echo NOTE: Component 03/04 (Making short film) is skipped
echo       as it is a practical production component
echo.
pause

python ocr-film-studies-manual.py

echo.
echo ================================
echo Test complete!
echo Check data-viewer-v2.html to see results
echo ================================
pause

