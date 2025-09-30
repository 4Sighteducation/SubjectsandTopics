@echo off
echo ================================
echo FULL AQA SCRAPER WITH RICH METADATA
echo ================================
echo.
echo This will scrape all 74 AQA subjects with:
echo - Web scraping for detailed topics (FREE)
echo - AI extraction from HTML for rules/metadata (~$0.06 each)
echo - PDF URLs stored (backup, no download unless needed)
echo.
echo Total cost: ~$4-5
echo Total time: 1-2 hours
echo.
echo Choose an option:
echo 1. TEST MODE (3 subjects - ~$0.20)
echo 2. FULL RUN (74 subjects - ~$4-5)
echo 3. Cancel
echo.

set /p choice="Enter your choice (1-3): "

if "%choice%"=="1" (
    echo.
    echo Running TEST MODE...
    python batch_processor.py --test
) else if "%choice%"=="2" (
    echo.
    echo Running FULL BATCH...
    echo This will take 1-2 hours and cost ~$4-5 in AI credits.
    echo You can stop at any time (Ctrl+C) and resume later.
    echo.
    pause
    python batch_processor.py
) else (
    echo Cancelled.
    exit /b
)

echo.
echo ================================
echo Processing complete!
echo ================================
pause
