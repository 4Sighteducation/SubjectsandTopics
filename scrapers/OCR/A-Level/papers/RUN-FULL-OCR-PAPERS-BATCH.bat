@echo off
REM Full OCR A-Level Papers Scraper Batch
REM Excludes Biology A and Ancient History (already done)
REM Only scrapes papers from 2019 onwards
REM Runs in HEADLESS mode

cd /d "%~dp0"

echo ========================================
echo OCR A-LEVEL PAPERS - FULL BATCH SCRAPER
echo ========================================
echo.
echo Running in HEADLESS mode (no browser windows)
echo Filtering: Papers from 2019 onwards only
echo Excluding: Biology A and Ancient History
echo.
echo This will take a while - please be patient...
echo.

set ERROR_COUNT=0
set SUCCESS_COUNT=0

REM Art and Design
echo [1/23] Art and Design...
python scrape-ocr-papers-universal.py H600 "Art and Design" "Art and Design - H200, H600 (from 2015)" "A Level"
if %ERRORLEVEL% EQU 0 (set /a SUCCESS_COUNT+=1) else (set /a ERROR_COUNT+=1)
echo.

REM Biology B (Advancing Biology)
echo [2/23] Biology B (Advancing Biology)...
python scrape-ocr-papers-universal.py H422 "Biology B" "Biology B (Advancing Biology) - H022, H422 (from 2015)" "A Level"
if %ERRORLEVEL% EQU 0 (set /a SUCCESS_COUNT+=1) else (set /a ERROR_COUNT+=1)
echo.

REM Business
echo [3/23] Business...
python scrape-ocr-papers-universal.py H431 "Business" "Business - H031, H431 (from 2015)" "A Level"
if %ERRORLEVEL% EQU 0 (set /a SUCCESS_COUNT+=1) else (set /a ERROR_COUNT+=1)
echo.

REM Chemistry A
echo [4/23] Chemistry A...
python scrape-ocr-papers-universal.py H432 "Chemistry A" "Chemistry A - H032, H432 (from 2015)" "A Level"
if %ERRORLEVEL% EQU 0 (set /a SUCCESS_COUNT+=1) else (set /a ERROR_COUNT+=1)
echo.

REM Chemistry B (Salters)
echo [5/23] Chemistry B (Salters)...
python scrape-ocr-papers-universal.py H433 "Chemistry B" "Chemistry B (Salters) - H033, H433 (from 2015)" "A Level"
if %ERRORLEVEL% EQU 0 (set /a SUCCESS_COUNT+=1) else (set /a ERROR_COUNT+=1)
echo.

REM Classical Civilisation
echo [6/23] Classical Civilisation...
python scrape-ocr-papers-universal.py H408 "Classical Civilisation" "Classical Civilisation - H008, H408 (from 2017)" "A Level"
if %ERRORLEVEL% EQU 0 (set /a SUCCESS_COUNT+=1) else (set /a ERROR_COUNT+=1)
echo.

REM Classical Greek
echo [7/23] Classical Greek...
python scrape-ocr-papers-universal.py H444 "Classical Greek" "Classical Greek - H044, H444 (from 2016)" "A Level"
if %ERRORLEVEL% EQU 0 (set /a SUCCESS_COUNT+=1) else (set /a ERROR_COUNT+=1)
echo.

REM Computer Science
echo [8/23] Computer Science...
python scrape-ocr-papers-universal.py H446 "Computer Science" "Computer Science - H046, H446 (from 2015)" "A Level"
if %ERRORLEVEL% EQU 0 (set /a SUCCESS_COUNT+=1) else (set /a ERROR_COUNT+=1)
echo.

REM Design and Technology
echo [9/23] Design and Technology...
python scrape-ocr-papers-universal.py H404 "Design and Technology" "Design and Technology - H004-H006, H404-H406 (from 2017)" "A Level"
if %ERRORLEVEL% EQU 0 (set /a SUCCESS_COUNT+=1) else (set /a ERROR_COUNT+=1)
echo.

REM Drama and Theatre
echo [10/23] Drama and Theatre...
python scrape-ocr-papers-universal.py H459 "Drama and Theatre" "Drama and Theatre - H059, H459 (from 2016)" "A Level"
if %ERRORLEVEL% EQU 0 (set /a SUCCESS_COUNT+=1) else (set /a ERROR_COUNT+=1)
echo.

REM Economics
echo [11/23] Economics...
python scrape-ocr-papers-universal.py H460 "Economics" "Economics - H060, H460 (from 2019)" "A Level"
if %ERRORLEVEL% EQU 0 (set /a SUCCESS_COUNT+=1) else (set /a ERROR_COUNT+=1)
echo.

REM English Language
echo [12/23] English Language...
python scrape-ocr-papers-universal.py H470 "English Language" "English Language - H070, H470 (from 2015)" "A Level"
if %ERRORLEVEL% EQU 0 (set /a SUCCESS_COUNT+=1) else (set /a ERROR_COUNT+=1)
echo.

REM English Language and Literature
echo [13/23] English Language and Literature...
python scrape-ocr-papers-universal.py H474 "English Language and Literature" "English Language and Literature (EMC) - H074, H474 (from 2015)" "A Level"
if %ERRORLEVEL% EQU 0 (set /a SUCCESS_COUNT+=1) else (set /a ERROR_COUNT+=1)
echo.

REM English Literature
echo [14/23] English Literature...
python scrape-ocr-papers-universal.py H472 "English Literature" "English Literature - H072, H472 (from 2015)" "A Level"
if %ERRORLEVEL% EQU 0 (set /a SUCCESS_COUNT+=1) else (set /a ERROR_COUNT+=1)
echo.

REM Film Studies
echo [15/23] Film Studies...
python scrape-ocr-papers-universal.py H410 "Film Studies" "Film Studies - H010, H410 (from 2017)" "A Level"
if %ERRORLEVEL% EQU 0 (set /a SUCCESS_COUNT+=1) else (set /a ERROR_COUNT+=1)
echo.

REM Further Mathematics A
echo [16/23] Further Mathematics A...
python scrape-ocr-papers-universal.py H245 "Further Mathematics A" "Further Mathematics A - H235, H245 (from 2017)" "A Level"
if %ERRORLEVEL% EQU 0 (set /a SUCCESS_COUNT+=1) else (set /a ERROR_COUNT+=1)
echo.

REM Further Mathematics B (MEI)
echo [17/23] Further Mathematics B (MEI)...
python scrape-ocr-papers-universal.py H645 "Further Mathematics B" "Further Mathematics B (MEI) - H635, H645 (from 2017)" "A Level"
if %ERRORLEVEL% EQU 0 (set /a SUCCESS_COUNT+=1) else (set /a ERROR_COUNT+=1)
echo.

REM Geography
echo [18/23] Geography...
python scrape-ocr-papers-universal.py H481 "Geography" "Geography - H081, H481 (from 2016)" "A Level"
if %ERRORLEVEL% EQU 0 (set /a SUCCESS_COUNT+=1) else (set /a ERROR_COUNT+=1)
echo.

REM Geology
echo [19/23] Geology...
python scrape-ocr-papers-universal.py H414 "Geology" "Geology - H014, H414 (from 2017)" "A Level"
if %ERRORLEVEL% EQU 0 (set /a SUCCESS_COUNT+=1) else (set /a ERROR_COUNT+=1)
echo.

REM History A
echo [20/23] History A...
python scrape-ocr-papers-universal.py H505 "History A" "History A - H105, H505 (from 2015)" "A Level"
if %ERRORLEVEL% EQU 0 (set /a SUCCESS_COUNT+=1) else (set /a ERROR_COUNT+=1)
echo.

REM Latin
echo [21/23] Latin...
python scrape-ocr-papers-universal.py H443 "Latin" "Latin - H043, H443  (from 2016)" "A Level"
if %ERRORLEVEL% EQU 0 (set /a SUCCESS_COUNT+=1) else (set /a ERROR_COUNT+=1)
echo.

REM Law
echo [22/23] Law...
python scrape-ocr-papers-universal.py H418 "Law" "Law - H018, H418 (from 2020)" "A Level"
if %ERRORLEVEL% EQU 0 (set /a SUCCESS_COUNT+=1) else (set /a ERROR_COUNT+=1)
echo.

REM Mathematics A
echo [23/23] Mathematics A...
python scrape-ocr-papers-universal.py H240 "Mathematics A" "Mathematics A - H230, H240 (from 2017)" "A Level"
if %ERRORLEVEL% EQU 0 (set /a SUCCESS_COUNT+=1) else (set /a ERROR_COUNT+=1)
echo.

REM Mathematics B (MEI)
echo [24/23] Mathematics B (MEI)...
python scrape-ocr-papers-universal.py H640 "Mathematics B" "Mathematics B (MEI) - H630, H640 (from 2017)" "A Level"
if %ERRORLEVEL% EQU 0 (set /a SUCCESS_COUNT+=1) else (set /a ERROR_COUNT+=1)
echo.

REM Media Studies
echo [25/23] Media Studies...
python scrape-ocr-papers-universal.py H409 "Media Studies" "Media Studies - H009, H409 (from 2023)" "A Level"
if %ERRORLEVEL% EQU 0 (set /a SUCCESS_COUNT+=1) else (set /a ERROR_COUNT+=1)
echo.

REM Music
echo [26/23] Music...
python scrape-ocr-papers-universal.py H543 "Music" "Music - H143, H543 (from 2016)" "A Level"
if %ERRORLEVEL% EQU 0 (set /a SUCCESS_COUNT+=1) else (set /a ERROR_COUNT+=1)
echo.

REM Physical Education
echo [27/23] Physical Education...
python scrape-ocr-papers-universal.py H555 "Physical Education" "Physical Education - H155, H555 (from 2016)" "A Level"
if %ERRORLEVEL% EQU 0 (set /a SUCCESS_COUNT+=1) else (set /a ERROR_COUNT+=1)
echo.

REM Physics A
echo [28/23] Physics A...
python scrape-ocr-papers-universal.py H556 "Physics A" "Physics A - H156, H556 (from 2015)" "A Level"
if %ERRORLEVEL% EQU 0 (set /a SUCCESS_COUNT+=1) else (set /a ERROR_COUNT+=1)
echo.

REM Physics B (Advancing Physics)
echo [29/23] Physics B (Advancing Physics)...
python scrape-ocr-papers-universal.py H557 "Physics B" "Physics B (Advancing Physics) - H157, H557 (from 2015)" "A Level"
if %ERRORLEVEL% EQU 0 (set /a SUCCESS_COUNT+=1) else (set /a ERROR_COUNT+=1)
echo.

REM Psychology
echo [30/23] Psychology...
python scrape-ocr-papers-universal.py H567 "Psychology" "Psychology - H167, H567 (from 2015)" "A Level"
if %ERRORLEVEL% EQU 0 (set /a SUCCESS_COUNT+=1) else (set /a ERROR_COUNT+=1)
echo.

REM Religious Studies
echo [31/23] Religious Studies...
python scrape-ocr-papers-universal.py H573 "Religious Studies" "Religious Studies - H173, H573 (from 2016)" "A Level"
if %ERRORLEVEL% EQU 0 (set /a SUCCESS_COUNT+=1) else (set /a ERROR_COUNT+=1)
echo.

REM Sociology
echo [32/23] Sociology...
python scrape-ocr-papers-universal.py H580 "Sociology" "Sociology - H180, H580 (from 2015)" "A Level"
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
echo Total subjects processed: 32
echo Excluded: Biology A, Ancient History
echo Filter: Papers from 2019 onwards only
echo.
pause





















