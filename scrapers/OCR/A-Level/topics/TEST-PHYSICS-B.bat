@echo off
echo ================================
echo Testing OCR Physics B (Advancing Physics) Scraper
echo ================================
echo.
echo This scraper creates ONE subject (H557) with 6 modules:
echo  - Module 1: Development of practical skills in physics
echo  - Module 2: Fundamental data analysis
echo  - Module 3: Physics in action
echo  - Module 4: Understanding processes
echo  - Module 5: Rise and fall of the clockwork universe
echo  - Module 6: Field and particle
echo.
echo Structure has 5 levels:
echo  - Level 0: Modules (6 total)
echo  - Level 1: Topics (H2 headings)
echo  - Level 2: Child topics of L1
echo  - Level 3: Under "Learning outcomes" heading (bold, no letter/numbering)
echo  - Level 4: Lettered/numbered list below L3 (a, b, c or 1, 2, 3)
echo.
echo NOTE: Content overview provides Level 0 and Level 1 hierarchy
echo       Content arranged in units with Level 1 topics as H2 headings
echo.
pause

python ocr-physics-b-manual.py

echo.
echo ================================
echo Test complete!
echo Check data-viewer-v2.html to see results
echo ================================
pause

