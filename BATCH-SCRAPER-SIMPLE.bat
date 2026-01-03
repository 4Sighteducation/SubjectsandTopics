@echo off
REM Simple Batch Scraper for AQA A-Level
REM Runs topics + papers for each subject
REM Note: You'll need to update the subject configs manually for now
REM
REM Or run the Python batch orchestrator:
REM python batch-scrape-aqa-alevel.py

echo ============================================================
echo AQA A-LEVEL COMPLETE SCRAPER
echo ============================================================
echo.
echo This will scrape ALL 42 A-level subjects.
echo Estimated time: 3-4 hours
echo.
echo Press Ctrl+C to cancel, or
pause

REM Biology (already done - example)
echo.
echo [1/42] Biology...
REM node crawl-aqa-biology-complete.js
REM python scrape-biology-everything.py

REM For other subjects, you'll need to:
REM 1. Create subject-specific scrapers, OR
REM 2. Use the Python batch orchestrator

echo.
echo ============================================================
echo For automated batch processing, run:
echo    python batch-scrape-aqa-alevel.py
echo ============================================================
pause

