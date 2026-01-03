@echo off
echo ================================
echo Testing OCR Psychology (2026+) Scraper
echo ================================
echo.
echo This scraper creates ONE subject (H569) with 3 components:
echo  - Component 1: Research methods
echo  - Component 2: Core studies in psychology
echo  - Component 3: Applied psychology
echo.
echo Component 1 Structure (4-5 levels):
echo  - Level 0: Component 1: Research methods
echo  - Level 1: Main topics (research methods and techniques, planning, etc.)
echo  - Level 2: Sub-topics
echo  - Level 3: Solid bullet points
echo  - Level 4: Open bullet points
echo.
echo Component 2 Structure (special handling):
echo  - Section A: Core Studies table (Area, Key Theme, Classic Study, Contemporary Study)
echo  - Section B: Areas, Perspectives and debates
echo  - Section C: Practical applications
echo  - NOTE: "Content" section after Core Studies table is IGNORED
echo.
echo Component 3 Structure:
echo  - Level 0: Component 3: Applied psychology (ONCE)
echo  - Level 1: Compulsory sections (Mental health, Criminal psychology)
echo  - Level 1: Optional sections (Child psychology, Environmental psychology, Sport and exercise psychology)
echo  - Level 2+: Sub-sections and topics
echo.
echo NOTE: "Learners should..." headings are filtered out
echo.
pause

python ocr-psychology-2026-manual.py

echo.
echo ================================
echo Test complete!
echo Check data-viewer-v2.html to see results
echo ================================
pause

