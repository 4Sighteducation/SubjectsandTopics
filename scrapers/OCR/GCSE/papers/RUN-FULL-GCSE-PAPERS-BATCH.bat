@echo off
REM Full OCR GCSE Papers Scraper Batch
REM Only scrapes papers from 2019 onwards
REM Runs in HEADLESS mode

cd /d "%~dp0"

echo ========================================
echo OCR GCSE PAPERS - FULL BATCH SCRAPER
echo ========================================
echo.
echo Running in HEADLESS mode (no browser windows)
echo Filtering: Papers from 2019 onwards only
echo.
echo This will take a while - please be patient...
echo.

set ERROR_COUNT=0
set SUCCESS_COUNT=0

REM Ancient History
echo [1/35] Ancient History...
python scrape-ocr-gcse-papers-universal.py J198 "Ancient History" "Ancient History (9-1) - J198 (from 2017)"
if %ERRORLEVEL% EQU 0 (set /a SUCCESS_COUNT+=1) else (set /a ERROR_COUNT+=1)
echo.

REM Art and Design
echo [2/35] Art and Design...
python scrape-ocr-gcse-papers-universal.py J170 "Art and Design" "Art and Design (9-1) - J170-J176 (from 2016)"
if %ERRORLEVEL% EQU 0 (set /a SUCCESS_COUNT+=1) else (set /a ERROR_COUNT+=1)
echo.

REM Biology A
echo [3/35] Biology A...
python scrape-ocr-gcse-papers-universal.py J247 "Biology A" "Gateway Science Suite - Biology A (9-1) - J247 (from 2016)"
if %ERRORLEVEL% EQU 0 (set /a SUCCESS_COUNT+=1) else (set /a ERROR_COUNT+=1)
echo.

REM Biology B
echo [4/35] Biology B...
python scrape-ocr-gcse-papers-universal.py J257 "Biology B" "Twenty First Century Science Suite - Biology B (9-1) - J257 (from 2016)"
if %ERRORLEVEL% EQU 0 (set /a SUCCESS_COUNT+=1) else (set /a ERROR_COUNT+=1)
echo.

REM Business
echo [5/35] Business...
python scrape-ocr-gcse-papers-universal.py J204 "Business" "Business (9-1) - J204 (from 2017)"
if %ERRORLEVEL% EQU 0 (set /a SUCCESS_COUNT+=1) else (set /a ERROR_COUNT+=1)
echo.

REM Chemistry A
echo [6/35] Chemistry A...
python scrape-ocr-gcse-papers-universal.py J248 "Chemistry A" "Gateway Science Suite - Chemistry A (9-1) - J248 (from 2016)"
if %ERRORLEVEL% EQU 0 (set /a SUCCESS_COUNT+=1) else (set /a ERROR_COUNT+=1)
echo.

REM Chemistry B
echo [7/35] Chemistry B...
python scrape-ocr-gcse-papers-universal.py J258 "Chemistry B" "Twenty First Century Science Suite - Chemistry B (9-1) - J258 (from 2016)"
if %ERRORLEVEL% EQU 0 (set /a SUCCESS_COUNT+=1) else (set /a ERROR_COUNT+=1)
echo.

REM Citizenship Studies
echo [8/35] Citizenship Studies...
python scrape-ocr-gcse-papers-universal.py J270 "Citizenship Studies" "Citizenship Studies (9-1) - J270 (from 2016)"
if %ERRORLEVEL% EQU 0 (set /a SUCCESS_COUNT+=1) else (set /a ERROR_COUNT+=1)
echo.

REM Classical Civilisation
echo [9/35] Classical Civilisation...
python scrape-ocr-gcse-papers-universal.py J199 "Classical Civilisation" "Classical Civilisation (9-1) - J199 (from 2017)"
if %ERRORLEVEL% EQU 0 (set /a SUCCESS_COUNT+=1) else (set /a ERROR_COUNT+=1)
echo.

REM Combined Science A
echo [10/35] Combined Science A...
python scrape-ocr-gcse-papers-universal.py J250 "Combined Science A" "Gateway Science Suite - Combined Science A (9-1) - J250 (from 2016)"
if %ERRORLEVEL% EQU 0 (set /a SUCCESS_COUNT+=1) else (set /a ERROR_COUNT+=1)
echo.

REM Combined Science B
echo [11/35] Combined Science B...
python scrape-ocr-gcse-papers-universal.py J260 "Combined Science B" "Twenty First Century Science Suite - Combined Science B (9-1) - J260 (from 2016)"
if %ERRORLEVEL% EQU 0 (set /a SUCCESS_COUNT+=1) else (set /a ERROR_COUNT+=1)
echo.

REM Computer Science
echo [12/35] Computer Science...
python scrape-ocr-gcse-papers-universal.py J277 "Computer Science" "Computer Science (9-1) - J277 (from 2020)"
if %ERRORLEVEL% EQU 0 (set /a SUCCESS_COUNT+=1) else (set /a ERROR_COUNT+=1)
echo.

REM Dance
echo [13/35] Dance...
python scrape-ocr-gcse-papers-universal.py J814 "Dance" "Dance (9-1) - J814 (from 2016)"
if %ERRORLEVEL% EQU 0 (set /a SUCCESS_COUNT+=1) else (set /a ERROR_COUNT+=1)
echo.

REM Design and Technology
echo [14/35] Design and Technology...
python scrape-ocr-gcse-papers-universal.py J310 "Design and Technology" "Design and Technology (9-1) - J310 (from 2017)"
if %ERRORLEVEL% EQU 0 (set /a SUCCESS_COUNT+=1) else (set /a ERROR_COUNT+=1)
echo.

REM Drama
echo [15/35] Drama...
python scrape-ocr-gcse-papers-universal.py J316 "Drama" "Drama (9-1) - J316 (from 2016)"
if %ERRORLEVEL% EQU 0 (set /a SUCCESS_COUNT+=1) else (set /a ERROR_COUNT+=1)
echo.

REM Economics
echo [16/35] Economics...
python scrape-ocr-gcse-papers-universal.py J205 "Economics" "Economics (9-1) - J205 (from 2017)"
if %ERRORLEVEL% EQU 0 (set /a SUCCESS_COUNT+=1) else (set /a ERROR_COUNT+=1)
echo.

REM English Language
echo [17/35] English Language...
python scrape-ocr-gcse-papers-universal.py J351 "English Language" "English Language (9-1) - J351"
if %ERRORLEVEL% EQU 0 (set /a SUCCESS_COUNT+=1) else (set /a ERROR_COUNT+=1)
echo.

REM English Literature
echo [18/35] English Literature...
python scrape-ocr-gcse-papers-universal.py J352 "English Literature" "English Literature (9-1) - J352 (from 2015)"
if %ERRORLEVEL% EQU 0 (set /a SUCCESS_COUNT+=1) else (set /a ERROR_COUNT+=1)
echo.

REM Food Preparation and Nutrition
echo [19/35] Food Preparation and Nutrition...
python scrape-ocr-gcse-papers-universal.py J309 "Food Preparation and Nutrition" "Food Preparation and Nutrition (9-1) - J309 (from 2016)"
if %ERRORLEVEL% EQU 0 (set /a SUCCESS_COUNT+=1) else (set /a ERROR_COUNT+=1)
echo.

REM French
echo [20/35] French...
python scrape-ocr-gcse-papers-universal.py J730 "French" "French (9-1) - J730 (from 2016)"
if %ERRORLEVEL% EQU 0 (set /a SUCCESS_COUNT+=1) else (set /a ERROR_COUNT+=1)
echo.

REM Geography A
echo [21/35] Geography A...
python scrape-ocr-gcse-papers-universal.py J383 "Geography A" "Geography A (Geographical Themes) (9-1) - J383 (from 2016)"
if %ERRORLEVEL% EQU 0 (set /a SUCCESS_COUNT+=1) else (set /a ERROR_COUNT+=1)
echo.

REM Geography B
echo [22/35] Geography B...
python scrape-ocr-gcse-papers-universal.py J384 "Geography B" "Geography B (Geography for Enquiring Minds) (9-1) - J384 (from 2016)"
if %ERRORLEVEL% EQU 0 (set /a SUCCESS_COUNT+=1) else (set /a ERROR_COUNT+=1)
echo.

REM German
echo [23/35] German...
python scrape-ocr-gcse-papers-universal.py J731 "German" "German - J731 (from 2016)"
if %ERRORLEVEL% EQU 0 (set /a SUCCESS_COUNT+=1) else (set /a ERROR_COUNT+=1)
echo.

REM History A
echo [24/35] History A...
python scrape-ocr-gcse-papers-universal.py J410 "History A" "History A (Explaining the Modern World) (9-1) - J410 (from 2016)"
if %ERRORLEVEL% EQU 0 (set /a SUCCESS_COUNT+=1) else (set /a ERROR_COUNT+=1)
echo.

REM History B
echo [25/35] History B...
python scrape-ocr-gcse-papers-universal.py J411 "History B" "History B (Schools History Project) (9-1) - J411 (from 2016)"
if %ERRORLEVEL% EQU 0 (set /a SUCCESS_COUNT+=1) else (set /a ERROR_COUNT+=1)
echo.

REM Latin
echo [26/35] Latin...
python scrape-ocr-gcse-papers-universal.py J282 "Latin" "Latin (9-1) - J282 (from 2016)"
if %ERRORLEVEL% EQU 0 (set /a SUCCESS_COUNT+=1) else (set /a ERROR_COUNT+=1)
echo.

REM Mathematics
echo [27/35] Mathematics...
python scrape-ocr-gcse-papers-universal.py J560 "Mathematics" "Mathematics (9-1) - J560 (from 2015)"
if %ERRORLEVEL% EQU 0 (set /a SUCCESS_COUNT+=1) else (set /a ERROR_COUNT+=1)
echo.

REM Media Studies
echo [28/35] Media Studies...
python scrape-ocr-gcse-papers-universal.py J200 "Media Studies" "Media Studies (9-1) - J200 (from 2023)"
if %ERRORLEVEL% EQU 0 (set /a SUCCESS_COUNT+=1) else (set /a ERROR_COUNT+=1)
echo.

REM Music
echo [29/35] Music...
python scrape-ocr-gcse-papers-universal.py J536 "Music" "Music (9-1) - J536 (from 2016)"
if %ERRORLEVEL% EQU 0 (set /a SUCCESS_COUNT+=1) else (set /a ERROR_COUNT+=1)
echo.

REM Physical Education
echo [30/35] Physical Education...
python scrape-ocr-gcse-papers-universal.py J587 "Physical Education" "Physical Education (9-1) - J587 (from 2016)"
if %ERRORLEVEL% EQU 0 (set /a SUCCESS_COUNT+=1) else (set /a ERROR_COUNT+=1)
echo.

REM Physics A
echo [31/35] Physics A...
python scrape-ocr-gcse-papers-universal.py J249 "Physics A" "Gateway Science Suite - Physics A (9-1) - J249 (from 2016)"
if %ERRORLEVEL% EQU 0 (set /a SUCCESS_COUNT+=1) else (set /a ERROR_COUNT+=1)
echo.

REM Physics B
echo [32/35] Physics B...
python scrape-ocr-gcse-papers-universal.py J259 "Physics B" "Twenty First Century Science Suite - Physics B (9-1) - J259 (from 2016)"
if %ERRORLEVEL% EQU 0 (set /a SUCCESS_COUNT+=1) else (set /a ERROR_COUNT+=1)
echo.

REM Religious Studies
echo [33/35] Religious Studies...
python scrape-ocr-gcse-papers-universal.py J625 "Religious Studies" "Religious Studies (9-1) - J625, J125 (from 2016)"
if %ERRORLEVEL% EQU 0 (set /a SUCCESS_COUNT+=1) else (set /a ERROR_COUNT+=1)
echo.

REM Sociology (Note: Listed as "Psychology" in dropdown but code is J203)
echo [34/35] Sociology...
python scrape-ocr-gcse-papers-universal.py J203 "Sociology" "Psychology (9-1) - J203 (from 2017)"
if %ERRORLEVEL% EQU 0 (set /a SUCCESS_COUNT+=1) else (set /a ERROR_COUNT+=1)
echo.

REM Spanish
echo [35/35] Spanish...
python scrape-ocr-gcse-papers-universal.py J732 "Spanish" "Spanish (9-1) - J732 (from 2016)"
if %ERRORLEVEL% EQU 0 (set /a SUCCESS_COUNT+=1) else (set /a ERROR_COUNT+=1)
echo.

echo.
echo ========================================
echo BATCH COMPLETE!
echo ========================================
echo.
echo Successfully scraped: %SUCCESS_COUNT% subjects
echo Errors: %ERROR_COUNT% subjects
echo.
echo Total subjects processed: 35
echo Filter: Papers from 2019 onwards only
echo.
pause

