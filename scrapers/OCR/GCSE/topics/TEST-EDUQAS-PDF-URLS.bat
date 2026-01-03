@echo off
REM Test script for Eduqas PDF URL scraper
REM This will test the scraper on a few subjects first

echo ========================================
echo Eduqas PDF URL Scraper - Test Run
echo ========================================
echo.

cd /d "%~dp0"

python eduqas-pdf-url-scraper.py --qualifications-file "Eduqas Qualifications - All.md" --output "eduqas-pdf-urls-test.json" --limit 5 --no-headless

echo.
echo ========================================
echo Test complete!
echo Check eduqas-pdf-urls-test.json for results
echo ========================================
pause

