@echo off
REM Run only the 3 failed subjects: English Language, Geography A, Geography B
REM These subjects now have hardcoded correct PDF URLs

echo ========================================
echo Eduqas GCSE Universal Scraper
echo Running Failed Subjects Only
echo ========================================
echo.
echo Subjects to process:
echo   - English Language
echo   - Geography A
echo   - Geography B
echo.

cd /d "%~dp0"

python eduqas-gcse-universal-scraper.py --subjects "English Language,Geography A,Geography B"

echo.
echo ========================================
echo Processing complete!
echo Check reports folder for results
echo ========================================
pause





















