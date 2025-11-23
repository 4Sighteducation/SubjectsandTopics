@echo off
REM Batch script to re-run scraper for subjects that had NO PAPERS found
REM These are the 6 subjects with empty finder-results divs

cd /d "%~dp0"

setlocal enabledelayedexpansion

set "SUCCESS_COUNT=0"
set "ERROR_COUNT=0"

echo ================================================================================
echo OCR GCSE - RE-RUNNING SUBJECTS WITH NO PAPERS FOUND
echo ================================================================================
echo.
echo This script will re-run the scraper for subjects that had empty results.
echo Using CORRECTED qualification filter names.
echo.
echo Subjects to process:
echo   1. J203 - Sociology (listed as Psychology in dropdown)
echo   2. J625 - Religious Studies
echo   3. J730 - French
echo   4. J731 - German
echo   5. J732 - Spanish
echo   6. J814 - Dance
echo.
echo ================================================================================
echo.

REM Subject 1: Sociology (J203) - Listed as "Psychology" in dropdown
echo [1/6] Sociology (J203)...
python scrape-ocr-gcse-papers-universal.py J203 "Sociology" "Psychology (9-1) - J203 (from 2017)" --min-year 2019
if %ERRORLEVEL% EQU 0 (
    set /a SUCCESS_COUNT+=1
    echo ✓ Success
) else (
    set /a ERROR_COUNT+=1
    echo ✗ Failed
)
echo.

REM Subject 2: Religious Studies (J625)
echo [2/6] Religious Studies (J625)...
python scrape-ocr-gcse-papers-universal.py J625 "Religious Studies" "Religious Studies (9-1) - J625, J125 (from 2016)" --min-year 2019
if %ERRORLEVEL% EQU 0 (
    set /a SUCCESS_COUNT+=1
    echo ✓ Success
) else (
    set /a ERROR_COUNT+=1
    echo ✗ Failed
)
echo.

REM Subject 3: French (J730)
echo [3/6] French (J730)...
python scrape-ocr-gcse-papers-universal.py J730 "French" "French (9-1) - J730 (from 2016)" --min-year 2019
if %ERRORLEVEL% EQU 0 (
    set /a SUCCESS_COUNT+=1
    echo ✓ Success
) else (
    set /a ERROR_COUNT+=1
    echo ✗ Failed
)
echo.

REM Subject 4: German (J731)
echo [4/6] German (J731)...
python scrape-ocr-gcse-papers-universal.py J731 "German" "German (9-1) - J731 (from 2016)" --min-year 2019
if %ERRORLEVEL% EQU 0 (
    set /a SUCCESS_COUNT+=1
    echo ✓ Success
) else (
    set /a ERROR_COUNT+=1
    echo ✗ Failed
)
echo.

REM Subject 5: Spanish (J732)
echo [5/6] Spanish (J732)...
python scrape-ocr-gcse-papers-universal.py J732 "Spanish" "Spanish (9-1) - J732 (from 2016)" --min-year 2019
if %ERRORLEVEL% EQU 0 (
    set /a SUCCESS_COUNT+=1
    echo ✓ Success
) else (
    set /a ERROR_COUNT+=1
    echo ✗ Failed
)
echo.

REM Subject 6: Dance (J814)
echo [6/6] Dance (J814)...
python scrape-ocr-gcse-papers-universal.py J814 "Dance" "Dance (9-1) - J814 (from 2016)" --min-year 2019
if %ERRORLEVEL% EQU 0 (
    set /a SUCCESS_COUNT+=1
    echo ✓ Success
) else (
    set /a ERROR_COUNT+=1
    echo ✗ Failed
)
echo.

echo ================================================================================
echo Batch process complete!
echo ================================================================================
echo Total subjects processed: %SUCCESS_COUNT% successful, %ERROR_COUNT% failed.
echo.
echo Check debug-output/ folder for HTML files showing what happened.
echo.
pause

