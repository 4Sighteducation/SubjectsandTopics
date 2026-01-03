"""Script to move Eduqas files to new folder structure."""
import shutil
from pathlib import Path

# Define paths
old_base = Path("scrapers/OCR/GCSE/topics")
new_gcse = Path("scrapers/Eduqas/GCSE/topics")
new_alevel = Path("scrapers/Eduqas/A-Level/topics")

# Create directories
new_gcse.mkdir(parents=True, exist_ok=True)
new_alevel.mkdir(parents=True, exist_ok=True)

# Files to move to GCSE folder
gcse_files = [
    "eduqas-gcse-universal-scraper.py",
    "eduqas-pdf-url-scraper.py",
    "eduqas-pdf-urls.json",
    "eduqas-pdf-urls-test.json",
    "Eduqas Qualifications - All.md",
    "Eduqas Qualifications.md",
    "EDUQAS-GCSE-HANDOVER.md",
    "EDUQAS-GCSE-UNIVERSAL-SCRAPER-README.md",
    "EDUQAS-PDF-URL-SCRAPER-README.md",
    "RUN-EDUQAS-GCSE-UNIVERSAL.bat",
    "RUN-EDUQAS-PDF-URLS.bat",
    "TEST-EDUQAS-GCSE-UNIVERSAL.bat",
    "TEST-EDUQAS-PDF-URLS.bat",
]

# Files to move to A-Level folder
alevel_files = [
    "eduqas-alevel-universal-scraper.py",
    "eduqas-pdf-url-scraper.py",  # Shared
    "Eduqas Qualifications - All.md",  # Shared
    "eduqas-pdf-urls.json",  # Shared (will be created/updated by both)
    "RUN-EDUQAS-ALEVEL-UNIVERSAL.bat",
    "TEST-EDUQAS-ALEVEL-UNIVERSAL.bat",
    "TEST-EDUQAS-ALEVEL-SINGLE.bat",
]

# Move GCSE files
print("Moving GCSE files...")
for file in gcse_files:
    old_path = old_base / file
    new_path = new_gcse / file
    if old_path.exists():
        shutil.copy2(old_path, new_path)
        print(f"  Copied: {file}")
    else:
        print(f"  Not found: {file}")

# Move A-Level files
print("\nMoving A-Level files...")
for file in alevel_files:
    old_path = old_base / file
    new_path = new_alevel / file
    if old_path.exists():
        shutil.copy2(old_path, new_path)
        print(f"  Copied: {file}")
    else:
        print(f"  Not found: {file}")

# Copy reports folder if it exists
reports_old = old_base / "reports"
if reports_old.exists():
    reports_new = new_gcse / "reports"
    if not reports_new.exists():
        shutil.copytree(reports_old, reports_new)
        print(f"\nCopied reports folder to GCSE")

print("\nDone! Files copied to new structure.")
print(f"GCSE: {new_gcse}")
print(f"A-Level: {new_alevel}")





















