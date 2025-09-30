@echo off
echo ================================
echo AQA Assessment Resources Scraper
echo ================================
echo.
echo This will scrape past papers and mark schemes for all 68 AQA subjects.
echo.
echo Time: ~2-3 hours
echo Cost: $0 (just web scraping, no AI)
echo.
echo Years: 2024, 2023, 2022
echo.
pause

python batch_assessment_resources.py

echo.
echo ================================
echo Assessment scraping complete!
echo Check the log file for details.
echo ================================
pause
