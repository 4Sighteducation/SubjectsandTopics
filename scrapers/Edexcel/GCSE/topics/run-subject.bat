@echo off
REM Universal Subject Scraper Runner
REM Usage: run-subject.bat <config-name>
REM Example: run-subject.bat geography-a

if "%1"=="" (
    echo Usage: run-subject.bat ^<config-name^>
    echo.
    echo Examples:
    echo   run-subject.bat geography-a
    echo   run-subject.bat geography-b
    echo   run-subject.bat business
    echo.
    pause
    exit /b 1
)

set CONFIG_NAME=%1
set CONFIG_FILE=configs\%CONFIG_NAME%.yaml

if not exist "%CONFIG_FILE%" (
    echo [ERROR] Config file not found: %CONFIG_FILE%
    echo.
    echo Available configs:
    dir /b configs\*.yaml
    pause
    exit /b 1
)

echo ========================================
echo EDEXCEL GCSE SUBJECT SCRAPER
echo ========================================
echo Config: %CONFIG_FILE%
echo ========================================
echo.

echo ========================================
echo STAGE 1: Upload Structure
echo ========================================
python universal-stage1-upload.py %CONFIG_FILE%
echo.
echo.

echo ========================================
echo STAGE 2: Extract PDF Content
echo ========================================
REM Check if config specifies a custom scraper
python -c "import yaml; config = yaml.safe_load(open('%CONFIG_FILE%', 'r', encoding='utf-8')); scraper = config.get('scraping', {}).get('custom_scraper', 'universal'); print(scraper)" > temp_scraper.txt
set /p CUSTOM_SCRAPER=<temp_scraper.txt
del temp_scraper.txt

if "%CUSTOM_SCRAPER%"=="mathematics" (
    echo Using Mathematics custom scraper...
    python mathematics-stage2-scrape.py %CONFIG_FILE%
) else (
    echo Using universal scraper...
    python universal-stage2-scrape.py %CONFIG_FILE%
)
echo.
echo.

echo ========================================
echo COMPLETE!
echo ========================================
pause


