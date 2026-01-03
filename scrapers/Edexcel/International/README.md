# Edexcel International Qualifications Scraper

This directory contains scrapers for **Edexcel International GCSE** and **International A Level** qualifications.

## 📁 Directory Structure

```
International/
├── International-GCSE/
│   ├── international-gcse-subjects.json    # 37 International GCSE subjects
│   └── topics/                              # Topic-specific scrapers (future)
│
├── International-A-Level/
│   ├── international-a-level-subjects.json  # 21 International A Level subjects
│   └── topics/                              # Topic-specific scrapers (future)
│
├── initialize-international-subjects.py     # Setup script for Supabase
├── universal-international-scraper.py       # Main topic scraper
├── run-batch-scraper.py                     # Batch processing with checkpoints
├── batch-results/                           # Batch run logs and summaries
└── README.md                                # This file
```

## 🚀 Quick Start

### Step 1: Initialize Subjects in Supabase

This creates the qualification types and uploads all subjects to the database:

```bash
python initialize-international-subjects.py
```

This will:
- ✅ Create "International GCSE" and "International A Level" qualification types
- ✅ Ensure Edexcel exam board exists
- ✅ Upload all 58 subjects to `exam_board_subjects` table

### Step 2: Scrape Topics

#### Single Subject

```bash
# International GCSE subject
python universal-international-scraper.py --subject IG-Biology

# International A Level subject
python universal-international-scraper.py --subject IAL-Physics
```

#### All Subjects in a Category

```bash
# All International GCSE subjects
python universal-international-scraper.py --all-igcse

# All International A Level subjects
python universal-international-scraper.py --all-ial

# Everything
python universal-international-scraper.py --all
```

#### Batch Mode (Recommended for Large Runs)

```bash
# Run International GCSE batch with logging and checkpoints
python run-batch-scraper.py --igcse

# Run International A Level batch
python run-batch-scraper.py --ial

# Run all batches
python run-batch-scraper.py --all

# Resume from last checkpoint (if interrupted)
python run-batch-scraper.py --resume

# Reset checkpoint and start fresh
python run-batch-scraper.py --reset
```

## 📊 Subjects Included

### International GCSE (37 subjects)
- Core subjects: Biology, Chemistry, Physics, Mathematics A/B
- Languages: Arabic, Chinese, French, German, Spanish, Greek, etc.
- Humanities: History, Geography, Religious Studies
- Business & Social: Business, Economics, Accounting, Commerce
- Technology: Computer Science, ICT
- Regional: Bangladesh Studies, Pakistan Studies, Islamic Studies
- And more...

### International A Level (21 subjects)
- Sciences: Biology, Chemistry, Physics
- Mathematics: Mathematics, Further Mathematics, Pure Mathematics
- Languages: Arabic, Chinese, French, German, Greek, Spanish
- Social Sciences: Business, Economics, Psychology, Law
- Humanities: History, Geography, English Language/Literature
- Technology: Information Technology
- And more...

## 🔧 How It Works

### 1. PDF Download & Extraction
- Downloads specification PDFs from Pearson website
- Extracts text using `pdfplumber` (preferred) or `PyPDF2` (fallback)

### 2. Topic Parsing
The scraper detects hierarchical structures:

```
Level 0: Paper/Component
  └─ Level 1: Topic
      └─ Level 2: Numbered items (1.1, 1.2, etc.)
          └─ Level 3: Sub-items and bullet points
```

Examples:
```
Paper 1: Mechanics                           [Level 0]
  Topic 1: Forces and motion                 [Level 1]
    1.1 Know Newton's laws of motion         [Level 2]
      • Apply to real-world scenarios        [Level 3]
```

### 3. Database Upload
Topics are uploaded to Supabase staging tables:
- `staging_aqa_subjects` - Subject metadata
- `staging_aqa_topics` - Topic hierarchy with parent relationships

## 📝 Configuration

### Subject JSON Format

Each subject has:
```json
{
  "code": "IG-Biology",
  "name": "Biology",
  "qualification": "International GCSE",
  "exam_board": "Edexcel",
  "pdf_url": "https://qualifications.pearson.com/..."
}
```

### Adding New Subjects

1. Add to the appropriate JSON file (`international-gcse-subjects.json` or `international-a-level-subjects.json`)
2. Run `python initialize-international-subjects.py` to upload to database
3. Run the scraper: `python universal-international-scraper.py --subject YOUR-CODE`

## 🔍 Monitoring Progress

### Batch Results
Check `batch-results/` for:
- `batch-run-TIMESTAMP.log` - Detailed execution log
- `summary-TIMESTAMP.json` - Results summary with success/failure counts
- `checkpoint.json` - Current progress (for resuming interrupted runs)

### Example Summary
```json
{
  "batch_name": "International GCSE",
  "summary": {
    "success": 35,
    "failed": 2,
    "total": 37
  },
  "results": [...]
}
```

## 🐛 Troubleshooting

### PDF Extraction Issues
Some PDFs may have:
- Complex layouts (tables, images)
- Unusual formatting
- Protected/encrypted content

**Solutions:**
1. Install both PDF libraries: `pip install pdfplumber PyPDF2`
2. Check the log files for specific errors
3. For complex subjects, you may need manual topic entry

### Missing Topics
If topics aren't detected:
1. Check the PDF structure manually
2. The parser may need adjustment for specific formatting
3. Consider creating a subject-specific scraper in `topics/`

### Database Errors
- Ensure `.env` file has valid Supabase credentials
- Check `staging_aqa_subjects` and `staging_aqa_topics` tables exist
- Verify exam board "Edexcel" exists in `exam_boards` table

## 📦 Requirements

```bash
pip install python-dotenv supabase requests PyPDF2 pdfplumber
```

## 🎯 Next Steps

1. **Initial Setup**: Run `initialize-international-subjects.py`
2. **Test Single Subject**: Try `--subject IG-Biology` to verify setup
3. **Batch Scrape**: Run `run-batch-scraper.py --all` for complete extraction
4. **Review Results**: Check topics in Supabase and refine as needed
5. **Manual Refinement**: For complex subjects, create custom scrapers in `topics/`

## 📚 Related Documentation

- Main scraper README: `../../README.md`
- GCSE scraper: `../GCSE/README.md`
- A-Level scraper: `../A-Level/README.md`

---

**Note**: International qualifications may have different structures than UK GCSE/A-Levels. The universal scraper handles most cases, but some subjects may require manual refinement.

