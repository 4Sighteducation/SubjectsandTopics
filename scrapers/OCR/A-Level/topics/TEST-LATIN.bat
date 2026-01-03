@echo off
echo ================================
echo Building OCR Latin Structure
echo ================================
echo.
echo This manually builds ONE subject (H443):
echo  - Prose Literature (Groups 1 & 2)
echo  - Verse Literature (Groups 3 & 4)
echo  - Accidence and Syntax
echo.
echo Structure:
echo  - Level 0: Main sections (3 total)
echo  - Level 1: Groups and grammar sections
echo  - Level 2: Individual texts and grammar topics
echo.
echo NOTE: This is a manual build, not a scraper
echo       Set texts are organized by exam year
echo.
pause

python ocr-latin-manual.py

echo.
echo ================================
echo Build complete!
echo Check data-viewer-v2.html to see results
echo ================================
pause

