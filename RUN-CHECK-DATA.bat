@echo off
echo ================================
echo FLASH Database Audit Tool
echo ================================
echo.
echo This will check what data already exists in Supabase
echo and generate a comprehensive HTML report.
echo.
pause

python check_existing_data.py

echo.
echo ================================
echo Audit complete!
echo Report opened in your browser.
echo ================================
pause
