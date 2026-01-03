@echo off
REM OCR A-Level Law (H418) Scraper Test
REM =====================================
REM 
REM This batch file runs the OCR Law scraper
REM 
REM Components:
REM - H418/01: The legal system and criminal law (starts page 9)
REM - H418/02: Law making and the law of tort
REM - H418/03: The nature of law and Human rights
REM - H418/04: The nature of law and the law of contract
REM 
REM =====================================

echo.
echo ======================================================================
echo                    OCR A-LEVEL LAW SCRAPER
echo ======================================================================
echo.
echo Subject: Law (H418)
echo Components: 4 (H418/01, H418/02, H418/03, H418/04)
echo.
echo Press any key to start scraping...
pause > nul

echo.
echo Starting scraper...
echo.

python ocr-law-manual.py

echo.
echo ======================================================================
echo                         SCRAPING COMPLETE
echo ======================================================================
echo.
echo Check the output above for results.
echo Debug files saved to: ..\debug-output\
echo.
pause

