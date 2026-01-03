@echo off
REM OCR A-Level Music (H543) Scraper Test
REM ======================================
REM 
REM This batch file runs the OCR Music scraper
REM 
REM Structure:
REM - Core Content
REM - 6 Areas of Study (3-6 include Set Works)
REM - Listening and appraising
REM 
REM ======================================

echo.
echo ======================================================================
echo                   OCR A-LEVEL MUSIC SCRAPER
echo ======================================================================
echo.
echo Subject: Music (H543)
echo.
echo Sections: 8 total
echo   - Core Content
echo   - Area 1: Haydn, Mozart, Beethoven + Prescribed Works (by year)
echo   - Area 2: Blues, Jazz, Swing + Prescribed Works (by year)
echo   - Area 3: Instrumental Jazz + Suggested Repertoire (List A/B)
echo   - Area 4: Baroque Religious + Suggested Repertoire (List A/B)
echo   - Area 5: Programme Music + Suggested Repertoire (List A/B)
echo   - Area 6: Innovations + Suggested Repertoire (List A/B)
echo   - Listening and appraising
echo.
echo Prescribed Works from section 5c (Areas 1-2)
echo Suggested Repertoire from section 5d (Areas 3-6)
echo.
echo Press any key to start scraping...
pause > nul

echo.
echo Starting scraper...
echo.

python ocr-music-manual.py

echo.
echo ======================================================================
echo                         SCRAPING COMPLETE
echo ======================================================================
echo.
echo Check the output above for results.
echo Debug files saved to: ..\debug-output\
echo.
pause

