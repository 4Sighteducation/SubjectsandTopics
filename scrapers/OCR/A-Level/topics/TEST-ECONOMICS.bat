@echo off
echo ================================
echo Testing OCR Economics Scraper
echo ================================
echo.
echo This scraper creates ONE subject (H460) with 2 components:
echo  - Component 1: Microeconomics
echo  - Component 2: Macroeconomics
echo.
echo Structure has 4 levels:
echo  - Level 0: Component name
echo  - Level 1: Main topic areas (5 per component)
echo  - Level 2: Numbered topics (e.g., "1.1 The economic problem")
echo  - Level 3: Learning outcome bullet points
echo.
echo NOTE: "Explain:" and "Evaluate:" headers
echo       are filtered out (not actual topics)
echo.
pause

python ocr-economics-manual.py

echo.
echo ================================
echo Test complete!
echo Check data-viewer-v2.html to see results
echo ================================
pause

