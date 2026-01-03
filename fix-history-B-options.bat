@echo off
echo ========================================
echo Fix History Paper 2 B Options
echo ========================================
echo Step 1: Deleting old B options with SQL...
echo.

REM You'll need to run the SQL manually in Supabase SQL editor:
REM Copy clean-history-paper2-B-options.sql content

echo Run this SQL in Supabase first, then press any key...
pause

echo.
echo Step 2: Re-uploading Paper 2 B options structure...
python scrapers\Edexcel\GCSE\topics\upload-history-structure.py

echo.
echo Step 3: Adding B options details...
python scrapers\Edexcel\GCSE\topics\upload-history-paper2-B-options.py

echo.
echo ========================================
echo COMPLETE!
echo ========================================
pause


