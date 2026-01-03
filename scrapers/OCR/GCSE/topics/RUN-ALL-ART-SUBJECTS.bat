@echo off
echo ========================================
echo OCR GCSE Art Subjects - Process ALL Subjects
echo ========================================
echo.
echo This will process all 7 Art subjects:
echo   J170 - Art, Craft and Design
echo   J171 - Fine Art
echo   J172 - Graphic Communication
echo   J173 - Photography
echo   J174 - Textile Design
echo   J175 - Three-Dimensional Design
echo   J176 - Critical and Contextual Studies
echo.
echo Each subject will extract ONLY its own content.
echo.

cd /d "%~dp0"

python ocr-art-subjects-manual.py

echo.
echo ========================================
echo All Art subjects processed!
echo ========================================
pause



