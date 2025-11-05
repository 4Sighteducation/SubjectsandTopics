@echo off
echo ============================================================
echo EDEXCEL A-LEVEL - BATCH TOPIC SCRAPER
echo ============================================================
echo Started: %date% %time%
echo.

cd A-Level\topics

REM Run each scraper (skip History and Biology A - already done)
echo [1/36] Arabic...
python scrape-9aa0.py

echo [2/36] Art and Design...
python scrape-9ad0.py

echo [3/36] Biology B...
python scrape-9bi0.py

echo [4/36] Business...
python scrape-9bs0.py

echo [5/36] Chemistry...
python scrape-9ch0.py

echo [6/36] Chinese...
python scrape-9cn0.py

echo [7/36] Design and Technology...
python scrape-9dt0.py

echo [8/36] Drama and Theatre...
python scrape-9dr0.py

echo [9/36] Economics A...
python scrape-9ec0.py

echo [10/36] Economics B...
python scrape-9eb0.py

echo [11/36] English Language...
python scrape-9en0.py

echo [12/36] English Language and Literature...
python scrape-9el0.py

echo [13/36] English Literature...
python scrape-9et0.py

echo [14/36] French...
python scrape-9fr0.py

echo [15/36] Geography...
python scrape-9ge0.py

echo [16/36] German...
python scrape-9gn0.py

echo [17/36] Greek...
python scrape-9gk0.py

echo [18/36] Gujarati...
python scrape-9gu0.py

echo [19/36] History of Art...
python scrape-9ht0.py

echo [20/36] Italian...
python scrape-9in0.py

echo [21/36] Japanese...
python scrape-9ja0.py

echo [22/36] Mathematics...
python scrape-9ma0.py

echo [23/36] Music...
python scrape-9mu0.py

echo [24/36] Music Technology...
python scrape-9mt0.py

echo [25/36] Persian...
python scrape-9pe0.py

echo [26/36] Physics...
python scrape-9ph0.py

echo [27/36] Politics...
python scrape-9pl0.py

echo [28/36] Portuguese...
python scrape-9pt0.py

echo [29/36] Psychology...
python scrape-9ps0.py

echo [30/36] Religious Studies...
python scrape-9rs0.py

echo [31/36] Russian...
python scrape-9ru0.py

echo [32/36] Spanish...
python scrape-9sp0.py

echo [33/36] Statistics...
python scrape-9st0.py

echo [34/36] Turkish...
python scrape-9tu0.py

echo [35/36] Urdu...
python scrape-9ur0.py

echo.
echo ============================================================
echo COMPLETE!
echo ============================================================
echo Completed: %date% %time%
echo.
echo Check Supabase for all topics with exam_board='Edexcel'
pause

