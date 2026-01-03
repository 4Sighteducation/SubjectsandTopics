@echo off
REM OCR A-Level Mathematics B (MEI) (H640) Scraper Test
REM ====================================================
REM 
REM This batch file runs the OCR Mathematics B (MEI) scraper
REM 
REM Areas:
REM - Area 1: Pure mathematics (11 topics)
REM - Area 2: Mechanics (7 topics)
REM - Area 3: Statistics (5 topics)
REM 
REM Structure has 5 levels (deeper than other scrapers)
REM 
REM ====================================================

echo.
echo ======================================================================
echo         OCR A-LEVEL MATHEMATICS B (MEI) SCRAPER
echo ======================================================================
echo.
echo Subject: Mathematics B (MEI) (H640)
echo Areas: 3 (Pure mathematics, Mechanics, Statistics)
echo.
echo Level 0: Areas (Pure, Mechanics, Statistics)
echo Level 1: Main topics (Proof, Algebra, Functions, etc.)
echo Level 2: Subsections (PROOF (1), PROOF (2), ALGEBRA (1), etc.)
echo Level 3: Specification items (Algebraic language, etc.)
echo Level 4: Ref codes (Mp1, p2, Ma1, Ma2, a3, a4, etc.)
echo.
echo Press any key to start scraping...
pause > nul

echo.
echo Starting scraper...
echo.

python ocr-maths-b-mei-manual.py

echo.
echo ======================================================================
echo                         SCRAPING COMPLETE
echo ======================================================================
echo.
echo Check the output above for results.
echo Debug files saved to: ..\debug-output\
echo.
pause

