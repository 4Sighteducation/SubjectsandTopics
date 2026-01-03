@echo off
REM OCR A-Level Mathematics A (H240) Scraper Test
REM ==============================================
REM 
REM This batch file runs the OCR Mathematics A scraper
REM 
REM Categories:
REM - Pure Mathematics (10 topics)
REM - Statistics (5 topics)
REM - Mechanics (4 topics)
REM 
REM Content starts page 20
REM 
REM ==============================================

echo.
echo ======================================================================
echo                OCR A-LEVEL MATHEMATICS A SCRAPER
echo ======================================================================
echo.
echo Subject: Mathematics A (H240)
echo Categories: 3 (Pure Mathematics, Statistics, Mechanics)
echo Topics: 19 total
echo.
echo Level 0: Categories (Pure Mathematics, Statistics, Mechanics)
echo Level 1: Topics (Proof, Algebra and functions, etc.)
echo Level 2: Subject Content (Indices, Surds, etc.)
echo Level 3: OCR Ref items (1.02a, 1.02b, etc.) with Stage 1+2 content
echo.
echo Press any key to start scraping...
pause > nul

echo.
echo Starting scraper...
echo.

python ocr-maths-a-manual.py

echo.
echo ======================================================================
echo                         SCRAPING COMPLETE
echo ======================================================================
echo.
echo Check the output above for results.
echo Debug files saved to: ..\debug-output\
echo.
pause

