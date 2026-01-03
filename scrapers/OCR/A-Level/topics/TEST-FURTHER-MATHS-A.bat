@echo off
REM OCR A-Level Further Mathematics A (H245) Scraper Test
REM ======================================================
REM 
REM This batch file runs the OCR Further Mathematics A scraper
REM 
REM Structure:
REM - Level 0: Mandatory papers, Optional papers
REM - Level 1: Pure mathematics, Statistics, Mechanics, etc.
REM - Level 2: Proof, Complex numbers, etc.
REM - Level 3: OCR Ref items (4.01a, 4.01b, etc.)
REM 
REM Content starts page 15, tables start page 17
REM Numbering starts at 4 (not 1)
REM 
REM ======================================================

echo.
echo ======================================================================
echo         OCR A-LEVEL FURTHER MATHEMATICS A SCRAPER
echo ======================================================================
echo.
echo Subject: Further Mathematics A (H245)
echo Sections: 2 (Mandatory papers, Optional papers)
echo.
echo Level 0: Mandatory/Optional papers
echo Level 1: Subject areas (Pure maths, Statistics, Mechanics, etc.)
echo Level 2: Topics (Proof, Complex numbers, etc.)
echo Level 3: OCR Ref items (4.01a, 4.01b, etc.) with Stage 1+2 content
echo.
echo Press any key to start scraping...
pause > nul

echo.
echo Starting scraper...
echo.

python ocr-further-maths-a-manual.py

echo.
echo ======================================================================
echo                         SCRAPING COMPLETE
echo ======================================================================
echo.
echo Check the output above for results.
echo Debug files saved to: ..\debug-output\
echo.
pause

