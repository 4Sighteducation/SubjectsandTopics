@echo off
echo ================================
echo AQA Batch Processor
echo ================================
echo.
echo Choose an option:
echo 1. TEST MODE (3 subjects only)
echo 2. FULL RUN (all 74 subjects)
echo 3. Cancel
echo.

set /p choice="Enter your choice (1-3): "

if "%choice%"=="1" (
    echo.
    echo Running in TEST MODE...
    python batch_processor.py --test
) else if "%choice%"=="2" (
    echo.
    echo Running FULL BATCH...
    echo This will take 2-4 hours. Press Ctrl+C to stop at any time.
    echo Progress is saved, so you can resume later.
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
echo Check the report that opened in your browser.
echo ================================
pause
