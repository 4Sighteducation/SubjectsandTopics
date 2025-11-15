#!/bin/bash
# Run each subject individually to avoid browser crashes cascading

cd "$(dirname "$0")"

echo "Running individual subject scrapers..."
echo "======================================"

# Subjects that should work (already tested or have papers)
subjects=(
    "GCSE-GeographyA"
    "GCSE-GeographyB"
    "GCSE-History"
    "GCSE-Mathematics"
    "GCSE-Music"
    "GCSE-PE"
    "GCSE-Physics"
    "GCSE-Chemistry"
    "GCSE-Biology"
    "GCSE-Science"
    "GCSE-DesignTech"
    "GCSE-Statistics"
    "GCSE-ReligiousStudiesA"
    "GCSE-ReligiousStudiesA-Short"
    "GCSE-ReligiousStudiesB"
    "GCSE-ReligiousStudiesB-Short"
)

for subject in "${subjects[@]}"; do
    echo ""
    echo "Scraping $subject..."
    python universal-gcse-paper-scraper.py "$subject"
    
    # Wait a bit between subjects
    sleep 2
done

echo ""
echo "======================================"
echo "All subjects processed!"

