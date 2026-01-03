@echo off
echo ========================================
echo OCR GCSE Art Subjects Scraper
echo ========================================
echo.
echo This will process all Art subjects (J170-J176):
echo   - Art, Craft and Design (J170)
echo   - Fine Art (J171)
echo   - Graphic Communication (J172)
echo   - Photography (J173)
echo   - Textile Design (J174)
echo   - Three-Dimensional Design (J175)
echo   - Critical and Contextual Studies (J176)
echo.
echo All subjects share the same PDF, so they will be processed together.
echo The PDF will be downloaded once, then each subject will get its own
echo filtered content with prefix: "GCSE Art and Design - [Subject Name] (GCSE)"
echo.
echo NOTE: Since all Art subjects share the same PDF URL, running without
echo --subject-code filter will process them all together automatically.
echo.
pause

cd /d "%~dp0"

echo.
echo Starting Art subjects scraper...
echo Processing all Art subjects (J170-J176) together...
echo.

REM Process only Art subjects - they share the same PDF so will be grouped together
python run-art-subjects.py

echo.
echo ========================================
echo Art subjects scraping complete!
echo ========================================
echo.
echo Check reports in: reports\
echo Reports created: J170-report.json through J176-report.json
echo.
pause

