# OCR Scraper Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Step 1: Install Dependencies

```bash
pip install anthropic openai google-generativeai pdfplumber pypdf
```

### Step 2: Configure API Key

Add **one** of these to your `.env` file:

```bash
# Option 1: Anthropic Claude (Recommended - Fast & Cheap)
ANTHROPIC_API_KEY=sk-ant-xxxxx

# Option 2: OpenAI GPT-4 (Most Powerful)
OPENAI_API_KEY=sk-xxxxx

# Option 3: Google Gemini (Free Tier Available)
GEMINI2.5_API_KEY=xxxxx
```

### Step 3: Test Single Subject

```bash
cd scrapers/OCR/A-Level/topics
python ocr-alevel-smart-scraper.py AL-BiologyA

# OR on Windows, use the test batch file:
TEST-BIOLOGY.bat
```

**Expected Output:**
```
🔬 OCR SMART SCRAPER: Biology A (H420)
================================================================================
STAGE 1: Scraping HTML 'specification at a glance' page
================================================================================
[INFO] Loading: https://www.ocr.org.uk/.../specification-at-a-glance/
[OK] Found content section
[INFO] Found 6 modules
[OK] Stage 1 extracted 45 topics from HTML
  - Content (L0): Content
  - Component01 (L0): Component 01 (Biological processes)
  - Module1 (L1): Module 1: Development of practical skills
  - Module2 (L1): Module 2: Foundations in biology
  ... and 41 more

================================================================================
STAGE 2: Scraping PDF for detailed sub-topics
================================================================================
[INFO] Downloading PDF...
[OK] Downloaded 5.0 MB
[INFO] Extracting PDF text with pdfplumber...
[OK] Extracted 245678 characters
[INFO] Extracting details for 6 modules...

[INFO] Processing: Module 1: Development of practical skills
[OK] Found 12 sub-topics for Module1

[INFO] Processing: Module 2: Foundations in biology
[OK] Found 45 sub-topics for Module2

... (processing other modules)

[OK] Stage 2 complete: 187 total topics

================================================================================
UPLOADING TO SUPABASE
================================================================================
[OK] Subject: Biology A (A-Level) (ID: 123)
[OK] Cleared old topics
[OK] Uploaded 187 topics
[OK] Linked 181 parent-child relationships

[INFO] Hierarchy distribution:
  Level 0: 3 topics
  Level 1: 6 topics
  Level 2: 42 topics
  Level 3: 98 topics
  Level 4: 38 topics

[SUCCESS] ✅ Two-stage scraping complete!
Total topics: 187
```

### Step 4: Run Batch (All 25 Subjects)

```bash
cd scrapers/OCR/A-Level/topics
python batch-ocr-topics.py
```

Press `Ctrl+C` anytime to pause (progress is saved).

Resume later with:
```bash
python batch-ocr-topics.py --resume
```

## 📊 What You'll Get

### Topics Scraped
- **Per Subject**: 50-200 topics with 3-4 hierarchy levels
- **Total**: ~2,500-3,500 topics across all 25 subjects

### Time Required
- **Single Subject**: 30-90 seconds
- **All Subjects**: 1-2 hours

### Cost (AI API)
- **Per Subject**: $0.10-0.50
- **All Subjects**: $3-12 total

## 🔍 Check Results

### Supabase Database
```sql
-- View subjects
SELECT * FROM staging_aqa_subjects 
WHERE exam_board = 'OCR' 
ORDER BY subject_name;

-- View topics for Biology A
SELECT t.topic_code, t.topic_name, t.topic_level
FROM staging_aqa_topics t
JOIN staging_aqa_subjects s ON t.subject_id = s.id
WHERE s.subject_code = 'H420'
ORDER BY t.topic_code;
```

### Debug Files
Check `scrapers/OCR/A-Level/topics/debug-output/`:
- `H420-spec.txt` - Extracted PDF text
- `H420-ai-output.txt` - AI's structured output

### Batch Results
Check `scrapers/OCR/A-Level/batch-results/`:
- `batch-topics-{timestamp}.log` - Full log
- `summary-topics-{timestamp}.json` - JSON summary

## 📚 Available Subjects (25 Total)

```json
{
  "AL-BiologyA": "Biology A (H420)",
  "AL-BiologyB": "Biology B - Advancing Biology (H422)",
  "AL-ChemistryA": "Chemistry A (H432)",
  "AL-ChemistryB": "Chemistry B - Salters (H433)",
  "AL-PhysicsA": "Physics A (H556)",
  "AL-PhysicsB": "Physics B - Advancing Physics (H557)",
  "AL-MathematicsA": "Mathematics A (H240)",
  "AL-FurtherMathematicsA": "Further Mathematics A (H245)",
  "AL-ComputerScience": "Computer Science (H446)",
  "AL-Economics": "Economics (H460)",
  "AL-Business": "Business (H431)",
  "AL-Business2026": "Business 2026+ (H436)",
  "AL-Geography": "Geography (H481)",
  "AL-HistoryA": "History A (H505)",
  "AL-Psychology": "Psychology (H567)",
  "AL-Psychology2026": "Psychology 2026+ (H569)",
  "AL-Sociology": "Sociology (H580)",
  "AL-Sociology2026": "Sociology 2026+ (H582)",
  "AL-EnglishLanguage": "English Language (H470)",
  "AL-EnglishLiterature": "English Literature (H472)",
  "AL-AncientHistory": "Ancient History (H407)",
  "AL-ClassicalCivilisation": "Classical Civilisation (H408)",
  "AL-Law": "Law (H418)",
  "AL-ReligiousStudies": "Religious Studies (H573)",
  "AL-PhysicalEducation": "Physical Education (H555)"
}
```

## 🔧 Troubleshooting

### Error: "No API keys found"
- Add one of the API keys to `.env` file
- Make sure the key starts with the correct prefix (`sk-ant-`, `sk-`, etc.)

### Error: "pdfplumber not installed"
```bash
pip install pdfplumber pypdf
```

### Error: "anthropic library not installed"
```bash
pip install anthropic
# OR
pip install openai
# OR
pip install google-generativeai
```

### Low topic count (< 50)
- Check `debug-output/{code}-ai-output.txt`
- AI might have misunderstood the format
- Try a different AI provider

### Supabase error
- Check `.env` has valid `SUPABASE_URL` and `SUPABASE_SERVICE_KEY`
- Verify tables exist: `staging_aqa_subjects`, `staging_aqa_topics`

## 📝 Next Steps

### 1. After Topics are Scraped
- ✅ Verify in Supabase
- ✅ Check hierarchy relationships
- ✅ Review any failed subjects

### 2. Create Papers Scraper
- Scrape past exam papers from OCR website
- Similar approach to Edexcel papers scraper
- Store in `staging_exam_papers` table

### 3. Add More Qualifications
- **GCSE**: OCR GCSE subjects
- **AS-Level**: H0XX specification codes
- **Cambridge Nationals**: Vocational qualifications

## 💡 Tips

### Best AI Provider
1. **Anthropic Claude** - Fast, cheap, reliable (Recommended)
2. **OpenAI GPT-4** - Most powerful, slightly more expensive
3. **Google Gemini** - Free tier available, good quality

### Optimize Speed
- Use Claude Haiku (fastest)
- Run batch overnight
- Use `--resume` flag if interrupted

### Debug Issues
1. Check debug files first
2. Review batch logs
3. Test single subject before batch
4. Verify PDF downloads correctly

## 📞 Support

Need help? Check:
1. `README.md` in `A-Level/` directory
2. Debug output in `topics/debug-output/`
3. Batch logs in `batch-results/`

---

**Ready to start? Run your first subject:**
```bash
cd scrapers/OCR/A-Level/topics
python ocr-alevel-topic-scraper.py AL-BiologyA
```

Good luck! 🚀

