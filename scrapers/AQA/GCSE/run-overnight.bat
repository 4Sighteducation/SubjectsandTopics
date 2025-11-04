@echo off
echo ========================================
echo    AQA GCSE OVERNIGHT SCRAPER
echo ========================================
echo.
echo Starting at %TIME%
echo.

cd /d "C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\scrapers\AQA\GCSE"

echo [1/2] Scraping GCSE Topics...
node run-all-gcse-topics.js > gcse-topics-log.txt 2>&1

echo.
echo [2/2] Scraping GCSE Papers...
python run-all-gcse-papers.py > gcse-papers-log.txt 2>&1

echo.
echo ========================================
echo    COMPLETE at %TIME%
echo ========================================
echo.
echo Check results in data-viewer.html
echo Select GCSE from filter dropdown
echo.
pause

