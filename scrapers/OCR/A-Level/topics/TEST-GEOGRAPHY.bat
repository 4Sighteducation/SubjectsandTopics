@echo off
echo ================================
echo Testing OCR Geography Scraper
echo ================================
echo.
echo This scraper creates ONE subject (H481) with 3 components:
echo  - Physical Systems
echo  - Human Interactions
echo  - Geographical Debates
echo.
echo Structure has 5 levels (extracts ALL):
echo  - Level 0: Component name
echo  - Level 1: Main topics (Landscape Systems, etc.)
echo  - Level 2: Sub-topics/Options (Option A, Option B, etc.)
echo  - Level 3: Key Ideas (a., b., c., etc.)
echo  - Level 4: Content bullets (from Content column)
echo.
echo NOTE: Extracts bullet points that appear AFTER
echo       the colon in the Content column
echo.
pause

python ocr-geography-manual.py

echo.
echo ================================
echo Test complete!
echo Check data-viewer-v2.html to see results
echo ================================
pause

