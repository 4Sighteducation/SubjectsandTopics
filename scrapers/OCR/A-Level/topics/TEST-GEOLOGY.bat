@echo off
echo ================================
echo Testing OCR Geology Scraper
echo ================================
echo.
echo This scraper creates ONE subject (H414):
echo  - All 7 modules extracted together
echo.
echo Structure has 5 levels:
echo  - Level 0: Modules (Module 1-7)
echo  - Level 1: Numbered topics (2.1, 2.2, etc.)
echo  - Level 2: Sub-topics (2.1.1, 2.1.2, etc.)
echo  - Level 3: Letter outcomes (a), (b), (c) from Learning outcomes
echo  - Level 4: Sub-outcomes (i), (ii) - ONLY when parent has title
echo.
echo SPECIAL RULE:
echo  - If letter has title ending in colon, (i), (ii) are Level 4
echo  - Otherwise, (i), (ii) remain Level 3
echo.
echo NOTE: Ignores "Additional guidance" column
echo.
pause

python ocr-geology-manual.py

echo.
echo ================================
echo Test complete!
echo Check data-viewer-v2.html to see results
echo ================================
pause

