@echo off
REM Full run script for Eduqas PDF URL scraper
REM This will scrape all qualifications

echo ========================================
echo Eduqas PDF URL Scraper - Full Run
echo ========================================
echo.
echo This will scrape PDF URLs for all Eduqas qualifications.
echo This may take a while...
echo.

cd /d "%~dp0"

python eduqas-pdf-url-scraper.py --qualifications-file "Eduqas Qualifications - All.md" --output "eduqas-pdf-urls.json"

echo.
echo ========================================
echo Scraping complete!
echo Check eduqas-pdf-urls.json for results
echo ========================================
pause





















