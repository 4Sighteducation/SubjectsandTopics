# OCR A-Level Scrapers

This directory contains scrapers for OCR (Oxford, Cambridge and RSA) A-Level qualifications.

## 📁 Structure

```
OCR/A-Level/
├── ocr-alevel-subjects.json     # All OCR A-Level subjects with PDF URLs
├── topics/
│   ├── ocr-alevel-topic-scraper.py   # AI-powered topic scraper
│   ├── batch-ocr-topics.py           # Batch runner for all subjects
│   └── debug-output/                 # Debug files (PDFs, AI outputs)
├── papers/
│   └── (to be created)              # Paper scrapers
└── README.md                        # This file
```

## 🔬 Topics Scraper

### ⭐ Smart Two-Stage Scraper (RECOMMENDED)

The smart scraper uses a **mandatory two-stage approach** for maximum reliability:

**Stage 1 (HTML)**: Scrapes "specification at a glance" page for clean module structure
**Stage 2 (PDF)**: Scrapes PDF specification for detailed sub-topics

### Features

- **Two-Stage**: HTML for structure + PDF for details = complete hierarchy
- **AI-Powered**: Uses Claude/GPT-4/Gemini to intelligently extract curriculum details
- **Complete**: Gets ALL hierarchy levels (Components → Modules → Topics → Sub-topics)
- **Reliable**: HTML parsing is cleaner than PDF-only approach

### Prerequisites

```bash
# Install required libraries
pip install anthropic openai google-generativeai pdfplumber pypdf

# Add API key to .env file (one of these):
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
GEMINI2.5_API_KEY=your_key_here
```

### Usage

**Single Subject:**
```bash
cd topics
python ocr-alevel-smart-scraper.py AL-BiologyA
python ocr-alevel-smart-scraper.py AL-ChemistryA
```

**All Subjects:**
```bash
cd topics
python ocr-alevel-smart-scraper.py --all
```

**Quick Test (Windows):**
```bash
cd topics
TEST-BIOLOGY.bat
```

**Batch Mode (with checkpointing):**
```bash
cd topics
python batch-ocr-topics.py
python batch-ocr-topics.py --resume  # Resume from checkpoint
```

### What Gets Scraped

**Stage 1 (HTML) extracts:**
- Components/Papers structure
- Modules (Module 1, Module 2, etc.)
- Key topics under each module

**Stage 2 (PDF) adds:**
- Detailed sub-topics for each module
- Learning objectives
- Practical investigations
- All content points

**Result:** Complete 4-level hierarchy with 150-250+ topics per subject

### Output

- Topics uploaded to `staging_aqa_topics` table in Supabase
- Debug files saved in `topics/debug-output/`:
  - `{code}-spec.txt` - Extracted PDF text
  - `{code}-ai-output.txt` - AI's structured output
- Batch results in `batch-results/`:
  - `batch-topics-{timestamp}.log` - Detailed log
  - `summary-topics-{timestamp}.json` - Summary JSON
  - `checkpoint-topics.json` - Progress checkpoint

## 📄 Available Subjects

### Core Sciences (7 subjects)
- Biology A (H420)
- Biology B - Advancing Biology (H422)
- Chemistry A (H432)
- Chemistry B - Salters (H433)
- Physics A (H556)
- Physics B - Advancing Physics (H557)

### Humanities (10 subjects)
- Ancient History (H407)
- Classical Civilisation (H408)
- Geography (H481)
- History A (H505)
- Law (H418)
- Psychology (H567)
- Psychology 2026+ (H569)
- Religious Studies (H573)
- Sociology (H580)
- Sociology 2026+ (H582)

### Arts & Languages (4 subjects)
- Art and Design (H600)
- Drama and Theatre (H459)
- English Language (H470)
- English Literature (H472)
- Media Studies (H409)

### Social Sciences (4 subjects)
- Business (H431)
- Business 2026+ (H436)
- Economics (H460)

### STEM (3 subjects)
- Computer Science (H446)
- Mathematics A (H240)
- Further Mathematics A (H245)

### Other (1 subject)
- Physical Education (H555)

**Total: 25 subjects**

## 🤖 How It Works

### 1. Download PDF
```python
# Downloads specification PDF from OCR website
pdf_content = scraper.download_pdf()
```

### 2. Extract Text
```python
# Extracts text using pdfplumber or pypdf
pdf_text = scraper.extract_text_from_pdf(pdf_content)
```

### 3. AI Processing
```python
# Sends to AI with structured prompt
hierarchy = scraper.extract_with_ai(pdf_text)
```

**AI Prompt:**
```
Extract curriculum content structure from this OCR A-Level PDF.

Create hierarchical numbered list:
1. Components/Modules
1.1 Main Topics
1.1.1 Sub-topics
1.1.1.1 Specific content

Rules:
- Include ONLY curriculum content
- Use decimal numbering (1.1.1.1)
- Keep titles concise
- Include all detail levels
```

### 4. Parse & Upload
```python
# Parses numbered hierarchy into structured topics
topics = scraper.parse_hierarchy(hierarchy)

# Uploads to Supabase with parent-child relationships
scraper.upload_to_supabase(topics)
```

## 📊 Expected Results

Per subject:
- **Topics**: 50-200 topics per subject
- **Levels**: 3-4 hierarchy levels
- **Time**: 30-90 seconds per subject
- **Cost**: $0.10-0.50 per subject (AI API)

Batch all subjects:
- **Total time**: 1-2 hours
- **Total cost**: $3-12 (depends on API)

## 🔍 Troubleshooting

### "No API keys found"
Add one of these to `.env`:
```
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GEMINI2.5_API_KEY=...
```

### "pdfplumber not installed"
```bash
pip install pdfplumber pypdf
```

### "No topics found in AI output"
Check debug files in `topics/debug-output/`:
1. `{code}-spec.txt` - Is text extracted correctly?
2. `{code}-ai-output.txt` - Did AI generate numbered list?

### Low topic count
- Some subjects have concise specifications
- Check `debug-output/{code}-ai-output.txt` to see what AI extracted
- You can manually refine the AI prompt if needed

## 📝 Next Steps

1. ✅ Topics scraper created and working
2. ⏳ Create papers scraper (similar to Edexcel approach)
3. ⏳ Add support for AS-Level specifications (H0XX codes)
4. ⏳ Create GCSE scrapers

## 🙋 Support

For issues:
1. Check debug output in `topics/debug-output/`
2. Check batch logs in `batch-results/`
3. Verify Supabase connection
4. Verify AI API key is valid

## 📚 Related Files

- `../../upload_papers_to_staging.py` - Upload helper
- `../../.env` - API keys and credentials
- Subject data: `ocr-alevel-subjects.json`

---

**Last Updated**: November 2025
**Exam Board**: OCR (Oxford, Cambridge and RSA)
**Qualification**: A-Level (Advanced Level)

