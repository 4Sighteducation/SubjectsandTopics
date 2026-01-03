@echo off
echo ========================================
echo OCR GCSE Universal Scraper - TEST MODE
echo ========================================
echo.
echo Excluded subjects (already perfect):
echo   - J260: Science B, Combined
echo   - J383: Geography A
echo.
echo Options:
echo   --subject-code JXXX  : Process only one subject
echo   --limit N            : Process first N subjects
echo   (no args)             : Process ALL subjects
echo.
echo Examples:
echo   .\TEST-GCSE-UNIVERSAL.bat --subject-code J170
echo   .\TEST-GCSE-UNIVERSAL.bat --limit 5
echo   .\TEST-GCSE-UNIVERSAL.bat
echo.
echo For full batch run, use: RUN-FULL-GCSE-BATCH.bat
echo.

python ocr-gcse-universal-scraper.py %*

echo.
echo ========================================
echo Test complete
echo ========================================
echo.
echo Reports saved to: reports\
pause

