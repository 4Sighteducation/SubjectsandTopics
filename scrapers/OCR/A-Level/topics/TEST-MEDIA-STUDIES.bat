@echo off
REM OCR A-Level Media Studies (H409) Scraper Test
REM ==============================================
REM 
REM This batch file runs the OCR Media Studies scraper
REM 
REM Extracts TWO hierarchies:
REM 1. Assessment Content (what students study)
REM 2. Subject Content Framework (theoretical framework)
REM 
REM ==============================================

echo.
echo ======================================================================
echo              OCR A-LEVEL MEDIA STUDIES SCRAPER
echo ======================================================================
echo.
echo Subject: Media Studies (H409)
echo Components: 2 (H409/01 Media messages, H409/02 Evolving media)
echo.
echo HIERARCHY 1 - Assessment Content:
echo   - H409/01: News (newspapers, online), Adverts, Magazines, Music Videos
echo   - H409/02: Film, Radio, Video Games, TV Drama
echo.
echo HIERARCHY 2 - Subject Content Framework:
echo   - Contexts of Media
echo   - Media Language (+ theories: Barthes, Todorov, Neale, etc.)
echo   - Media Representations
echo   - Media Industries
echo   - Media Audiences
echo.
echo Press any key to start scraping...
pause > nul

echo.
echo Starting scraper...
echo.

python ocr-media-studies-manual.py

echo.
echo ======================================================================
echo                         SCRAPING COMPLETE
echo ======================================================================
echo.
echo Check the output above for results.
echo Debug files saved to: ..\debug-output\
echo.
pause

