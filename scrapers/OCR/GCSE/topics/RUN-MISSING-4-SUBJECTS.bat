@echo off
REM Run only the 4 missing subjects: English Literature, Geology, Mathematics, Sociology
REM These subjects now have hardcoded correct PDF URLs

echo ========================================
echo Eduqas GCSE Universal Scraper
echo Running Missing 4 Subjects Only
echo ========================================
echo.
echo Subjects to process:
echo   - English Literature
echo   - Geology
echo   - Mathematics
echo   - Sociology
echo.

cd /d "%~dp0"

python eduqas-gcse-universal-scraper.py --subjects "English Literature,Geology,Mathematics,Sociology"

echo.
echo ========================================
echo Processing complete!
echo Check reports folder for results
echo ========================================
pause





















