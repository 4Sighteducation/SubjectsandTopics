# OCR (Oxford, Cambridge and RSA) Scrapers

Scrapers for OCR exam board qualifications using AI-powered topic extraction.

## 📁 Structure

```
OCR/
├── README.md                    # This file
├── QUICK-START.md              # Quick start guide
├── A-Level/                    # A-Level qualifications
│   ├── ocr-alevel-subjects.json
│   ├── topics/                 # Topic scrapers
│   │   ├── ocr-alevel-topic-scraper.py
│   │   ├── batch-ocr-topics.py
│   │   └── debug-output/
│   ├── papers/                 # Paper scrapers (TBD)
│   ├── batch-results/          # Batch run results
│   └── README.md
├── GCSE/                       # GCSE qualifications (TBD)
└── AS-Level/                   # AS-Level qualifications (TBD)
```

## 🚀 Quick Start

See **[QUICK-START.md](QUICK-START.md)** for a 5-minute setup guide.

### TLDR;
```bash
# Install
pip install anthropic pdfplumber pypdf

# Add to .env
ANTHROPIC_API_KEY=sk-ant-xxxxx

# Run single subject
cd A-Level/topics
python ocr-alevel-topic-scraper.py AL-BiologyA

# Run all subjects (25 total)
python batch-ocr-topics.py
```

## 📊 What's Available

### ✅ A-Level (25 Subjects)
- **Core Sciences**: Biology A/B, Chemistry A/B, Physics A/B
- **Mathematics**: Mathematics A, Further Mathematics A
- **Humanities**: History, Geography, Ancient History, Classical Civilisation, Law
- **Social Sciences**: Psychology, Sociology, Economics, Business
- **Languages**: English Language, English Literature
- **Arts**: Art and Design, Drama and Theatre, Media Studies
- **Other**: Computer Science, Physical Education, Religious Studies

See full list in `A-Level/ocr-alevel-subjects.json`

### ⏳ Coming Soon
- **GCSE**: OCR GCSE subjects
- **AS-Level**: H0XX specification codes
- **Papers**: Past exam papers scraper

## 🔬 How It Works

### AI-Powered Extraction
1. **Download PDF** specification from OCR website
2. **Extract text** using pdfplumber/pypdf
3. **AI processing** with Claude/GPT-4/Gemini to understand structure
4. **Parse hierarchy** into numbered topics
5. **Upload to Supabase** with parent-child relationships

### Why AI?
- **Smart**: Understands document structure, not just pattern matching
- **Flexible**: Works with different PDF formats and layouts
- **Complete**: Captures all hierarchy levels
- **Fast**: 30-90 seconds per subject

## 📈 Results

### Expected Output (per subject)
```
Topics: 50-200 structured topics
Levels: 3-4 hierarchy levels
Time: 30-90 seconds
Cost: $0.10-0.50
```

### Example: Biology A (H420)
```
1. Component 01: Biological processes
1.1 Module 2: Foundations in biology
1.1.1 Cell structure
1.1.1.1 The microscope in cell studies
1.1.1.2 Eukaryotic cells
1.1.1.3 Prokaryotic cells
1.1.2 Biological molecules
1.1.2.1 Water
1.1.2.2 Carbohydrates
...
```

## 🛠️ Setup

### Prerequisites
```bash
pip install anthropic openai google-generativeai pdfplumber pypdf
```

### Environment Variables
Add to `.env` file:
```bash
# Database
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=xxx

# AI Provider (choose one)
ANTHROPIC_API_KEY=sk-ant-xxx        # Recommended
OPENAI_API_KEY=sk-xxx               # Alternative
GEMINI2.5_API_KEY=xxx               # Alternative
```

## 🎯 Usage

### Single Subject
```bash
cd A-Level/topics
python ocr-alevel-topic-scraper.py AL-BiologyA
python ocr-alevel-topic-scraper.py AL-ChemistryA
python ocr-alevel-topic-scraper.py AL-Psychology
```

### All Subjects
```bash
cd A-Level/topics
python ocr-alevel-topic-scraper.py --all
```

### Batch Mode (with checkpointing)
```bash
cd A-Level/topics
python batch-ocr-topics.py
# Press Ctrl+C to pause, progress is saved
python batch-ocr-topics.py --resume
```

## 📂 Output Files

### Database
- `staging_aqa_subjects` - Subject metadata
- `staging_aqa_topics` - Hierarchical topics

### Debug Files
`A-Level/topics/debug-output/`:
- `{code}-spec.txt` - Extracted PDF text
- `{code}-ai-output.txt` - AI's structured response

### Batch Results
`A-Level/batch-results/`:
- `batch-topics-{timestamp}.log` - Detailed log
- `summary-topics-{timestamp}.json` - Summary with stats
- `checkpoint-topics.json` - Resume checkpoint

## 🔍 Verification

### Check Supabase
```sql
-- View all OCR subjects
SELECT subject_code, subject_name, qualification_type
FROM staging_aqa_subjects
WHERE exam_board = 'OCR'
ORDER BY subject_name;

-- View topics for a subject
SELECT t.topic_code, t.topic_name, t.topic_level,
       p.topic_name as parent_name
FROM staging_aqa_topics t
JOIN staging_aqa_subjects s ON t.subject_id = s.id
LEFT JOIN staging_aqa_topics p ON t.parent_topic_id = p.id
WHERE s.subject_code = 'H420'
ORDER BY t.topic_code;
```

## 📊 Statistics

### Batch Run Metrics
```
Total Subjects: 25
Total Topics: ~2,500-3,500
Total Time: 1-2 hours
Total Cost: $3-12
Success Rate: 95%+
```

### Per Subject Average
```
Topics: 100-140
Time: 45-60 seconds
Cost: $0.15-0.30
```

## 🐛 Troubleshooting

### Common Issues

**"No API keys found"**
- Add API key to `.env` file
- Restart terminal/script

**"pdfplumber not installed"**
```bash
pip install pdfplumber pypdf
```

**Low topic count (< 50)**
- Check `debug-output/{code}-ai-output.txt`
- Try different AI provider
- Check if PDF downloaded correctly

**Supabase connection error**
- Verify `.env` credentials
- Check internet connection
- Verify tables exist

### Debug Steps
1. Run single subject first
2. Check debug files in `debug-output/`
3. Review batch logs
4. Verify PDF text extraction
5. Check AI output format

## 🔮 Roadmap

### Phase 1: Topics ✅
- [x] AI-powered scraper
- [x] Batch runner with checkpointing
- [x] 25 A-Level subjects
- [x] Debug output

### Phase 2: Papers ⏳
- [ ] OCR past papers scraper
- [ ] Question papers, mark schemes, reports
- [ ] Group by year/series
- [ ] Upload to `staging_exam_papers`

### Phase 3: Expansion ⏳
- [ ] GCSE subjects
- [ ] AS-Level specs
- [ ] Cambridge Nationals
- [ ] Updated specifications (2026+)

## 📚 Resources

### Documentation
- [A-Level README](A-Level/README.md) - Detailed A-Level docs
- [QUICK-START.md](QUICK-START.md) - Quick setup guide

### OCR Resources
- **Website**: https://www.ocr.org.uk
- **Qualifications**: https://www.ocr.org.uk/qualifications/
- **Past Papers**: https://www.ocr.org.uk/students/past-papers/

### AI Providers
- **Anthropic**: https://console.anthropic.com/
- **OpenAI**: https://platform.openai.com/
- **Google AI**: https://ai.google.dev/

## 🤝 Contributing

### Adding New Subjects
1. Add to `A-Level/ocr-alevel-subjects.json`:
```json
{
  "AL-NewSubject": {
    "name": "Subject Name",
    "code": "H999",
    "as_code": "H099",
    "qualification": "A-Level",
    "exam_board": "OCR",
    "at_a_glance_url": "https://...",
    "pdf_url": "https://..."
  }
}
```
2. Run scraper: `python ocr-alevel-topic-scraper.py AL-NewSubject`

### Testing Changes
```bash
# Test single subject
python ocr-alevel-topic-scraper.py AL-BiologyA

# Verify output
cat debug-output/H420-ai-output.txt
```

## 📞 Support

For issues:
1. Check [QUICK-START.md](QUICK-START.md)
2. Review debug output
3. Check batch logs
4. Verify API keys

## 📄 License

Part of the flash-curriculum-pipeline project.

---

**Last Updated**: November 2025  
**Exam Board**: OCR (Oxford, Cambridge and RSA)  
**Status**: A-Level topics ✅ | Papers ⏳ | GCSE ⏳

