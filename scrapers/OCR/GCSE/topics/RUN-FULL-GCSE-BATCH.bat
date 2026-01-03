@echo off
echo ========================================
echo OCR GCSE Universal Scraper - FULL BATCH
echo ========================================
echo.
echo This will process ALL OCR GCSE subjects (except excluded ones).
echo.
echo Excluded subjects (already perfect):
echo   - J260: Science B, Combined
echo   - J383: Geography A
echo.
echo Estimated time: 1-2 hours
echo.
echo Subjects that share PDFs:
echo   - Art strands (J170-J176): 7 subjects, 1 PDF
echo   - Religious Studies (J625, J125): 2 subjects, 1 PDF
echo.
pause

python ocr-gcse-universal-scraper.py

echo.
echo ========================================
echo Full batch complete!
echo ========================================
echo.
echo Check reports in: reports\
echo Check summary: reports\summary-*.json
echo.
pause



