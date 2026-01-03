@echo off
REM OCR A-Level Further Mathematics B (MEI) (H645) Scraper Test
REM ===========================================================
REM 
REM This batch file runs the OCR Further Mathematics B (MEI) scraper
REM 
REM Papers:
REM - Mandatory: Core pure (Y420)
REM - Major options: Mechanics major (Y421), Statistics major (Y422)
REM - Minor options: 6 papers (Y431-Y436)
REM 
REM Structure has 5 levels
REM 
REM ===========================================================

echo.
echo ======================================================================
echo      OCR A-LEVEL FURTHER MATHEMATICS B (MEI) SCRAPER
echo ======================================================================
echo.
echo Subject: Further Mathematics B (MEI) (H645)
echo Papers: 9 total (1 mandatory + 2 major options + 6 minor options)
echo.
echo Level 0: Papers (Core pure, Mechanics major, Statistics major, etc.)
echo Level 1: Main topics (Proof, Complex numbers, Dimensional analysis, etc.)
echo Level 2: Subsections (a), (b), (c)
echo Level 3: Specification items
echo Level 4: Ref codes (Mq1, q2, q3, etc.)
echo.
echo Press any key to start scraping...
pause > nul

echo.
echo Starting scraper...
echo.

python ocr-further-maths-b-mei-manual.py

echo.
echo ======================================================================
echo                         SCRAPING COMPLETE
echo ======================================================================
echo.
echo Check the output above for results.
echo Debug files saved to: ..\debug-output\
echo.
pause

