# How to Commit Your Work

## Simple Git Workflow

Open a **new terminal/command prompt** and run these commands:

### 1. Add only the scraper files

```bash
# Geography scrapers
git add scrapers/Edexcel/GCSE/topics/universal-stage1-upload.py
git add scrapers/Edexcel/GCSE/topics/universal-stage2-scrape.py
git add scrapers/Edexcel/GCSE/topics/run-subject.bat
git add scrapers/Edexcel/GCSE/topics/configs/
git add scrapers/Edexcel/GCSE/topics/UNIVERSAL-SCRAPER-README.md
git add scrapers/Edexcel/GCSE/topics/SUBJECT-CONFIG-TEMPLATE.yaml

# History uploaders
git add scrapers/Edexcel/GCSE/topics/upload-history*.py
git add scrapers/Edexcel/GCSE/topics/add-paper2-sections-only.py

# Batch runners
git add run-*.bat
git add add-*.bat
git add test-*.bat

# Documentation
git add EDEXCEL-GCSE-SCRAPER-HANDOVER.md

# SQL helpers
git add clean-history-paper2-B-options.sql
```

### 2. Commit

```bash
git commit -m "feat: Universal Geography scraper + Complete History structure

- Universal YAML-based Geography scraper (A & B working)
- Complete GCSE History structure (3 Papers, 15 Options)
- Incremental manual upload system for complex subjects
- Comprehensive handover documentation"
```

### 3. Push to GitHub

```bash
git push origin main
```

---

## Or Use GitHub Desktop / VS Code

If you prefer a GUI:
1. Open GitHub Desktop or VS Code
2. Review changed files
3. Uncheck any files you don't want (like node_modules, temp files)
4. Commit with message
5. Push

---

## What to Commit

**DO commit:**
- `scrapers/Edexcel/GCSE/topics/*.py` (all new Python files)
- `scrapers/Edexcel/GCSE/topics/configs/*.yaml`
- `*.bat` files (runners)
- `*.md` files (documentation)
- `*.sql` files (helpers)

**DON'T commit:**
- `node_modules/`
- `__pycache__/`
- `*.pyc`
- Temp files
- `nul` file

---

**Note:** The batch file I created tried to commit EVERYTHING which caused the error. Manual is safer!


