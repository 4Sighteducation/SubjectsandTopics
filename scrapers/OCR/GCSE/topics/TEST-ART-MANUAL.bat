@echo off
echo ========================================
echo OCR GCSE Art Subjects Manual Scraper Test
echo ========================================
echo.
echo Options:
echo   --subject-code JXXX  : Process only one subject (e.g., J174)
echo   (no args)            : Process ALL Art subjects
echo.

cd /d "%~dp0"

python ocr-art-subjects-manual.py %*

echo.
echo ========================================
echo Test complete!
echo ========================================
pause



