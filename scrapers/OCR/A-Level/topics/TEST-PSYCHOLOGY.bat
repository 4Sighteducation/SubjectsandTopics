@echo off
echo ================================
echo Testing OCR Psychology Scraper
echo ================================
echo.
echo This scraper creates ONE subject (H567) with 3 components:
echo  - Component 01: Research methods
echo  - Component 02: Psychological themes through core studies
echo  - Component 03: Applied psychology
echo.
echo Component 01 Structure (4-5 levels):
echo  - Level 0: Component 01: Research methods
echo  - Level 1: Main topics (Self-report, Experiment, Observation, Correlation)
echo  - Level 2: Sub-topics
echo  - Level 3: Solid bullet points
echo  - Level 4: Open bullet points
echo.
echo Component 02 Structure (special handling):
echo  - Section A: Core Studies table (Area, Key Theme, Classic Study, Contemporary Study)
echo  - Section B: Areas, Perspectives and debates
echo  - Section C: Practical applications
echo  - NOTE: "Content" section after Core Studies table is IGNORED
echo.
echo Component 03 Structure (table-based, 5 levels):
echo  - Level 1: Section name
echo  - Level 2: Topic (from Topic column)
echo  - Level 3: Background bullet points
echo  - Level 4: Key research items
echo  - Level 5: Application items
echo.
echo NOTE: "Learners should..." headings are filtered out
echo.
pause

python ocr-psychology-manual.py

echo.
echo ================================
echo Test complete!
echo Check data-viewer-v2.html to see results
echo ================================
pause

