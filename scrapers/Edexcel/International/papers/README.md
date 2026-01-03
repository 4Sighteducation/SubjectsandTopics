# International GCSE Exam Papers Scraper

Comprehensive scraper for all Edexcel International GCSE exam papers, mark schemes, and examiner reports.

## Features

✅ **Scrapes 25 International GCSE subjects**  
✅ **Extracts**: Question Papers, Mark Schemes, Examiner Reports  
✅ **Handles**: Multiple papers (Paper 1, Paper 2, etc.)  
✅ **Supports**: Multiple options (History, etc.)  
✅ **Uploads**: Directly to database (`staging_aqa_exam_papers`)  
✅ **Progress tracking**: Resume from checkpoint on interruption  

## Supported Subjects

| Subject Code | Subject Name | Paper Code |
|--------------|--------------|------------|
| IG-Accounting | Accounting | 4ac1 |
| IG-Arabic | Arabic | 4ar1 |
| IG-Biology | Biology | 4bi1 |
| IG-Business | Business Studies | 4bs1 |
| IG-Chemistry | Chemistry | 4ch1 |
| IG-Chinese | Chinese | 4cn1 |
| IG-Commerce | Commerce | 4cm1 |
| IG-ComputerScience | Computer Science | 4cs1 |
| IG-Economics | Economics | 4ec1 |
| IG-EnglishESL | English as a Second Language | 4es1 |
| IG-EnglishLanguageA | English Language A | 4ea1 |
| IG-EnglishLanguageB | English Language B | 4eb1 |
| IG-EnglishLiterature | English Literature | 4et1 |
| IG-French | French | 4fr1 |
| IG-Geography | Geography | 4ge1 |
| IG-German | German | 4gn1 |
| IG-History | History | 4hi1 |
| IG-HumanBiology | Human Biology | 4hb1 |
| IG-ICT | Information and Communication Technology | 4it1 |
| IG-MathematicsA | Mathematics A | 4ma1 |
| IG-MathematicsB | Mathematics B | 4mb1 |
| IG-FurtherPureMaths | Further Pure Mathematics | 4pm1 |
| IG-Physics | Physics | 4ph1 |
| IG-Spanish | Spanish | 4sp1 |
| IG-ScienceDoubleAward | Science (Double Award) | 4sc1 |

## Filename Formats Supported

The scraper handles multiple International GCSE filename formats:

```
4FR1_02_que_20210505.pdf     → French Paper 2, Question Paper, May 2021
4fr1-02-rms-20210604.pdf     → French Paper 2, Mark Scheme, June 2021
4hi1-02-pef-20230824.pdf     → History Paper 2, Examiner Report, Aug 2023
4ma1_1h_que_20220511.pdf     → Maths A Paper 1H (Higher), Question Paper, May 2022
4hi1-2a-que-20230608.pdf     → History Paper 2 Option A, Question Paper, June 2023
```

**Document Type Codes:**
- `que` = Question Paper
- `rms` = Mark Scheme  
- `pef` / `per` = Examiner Report

## Usage

### Single Subject

Scrape one subject's papers:

```bash
cd scrapers/Edexcel/International/papers
python universal-igcse-paper-scraper.py IG-French
python universal-igcse-paper-scraper.py IG-History
python universal-igcse-paper-scraper.py IG-Biology
```

### All Subjects (Batch)

Scrape all 25 subjects at once:

```bash
python batch-igcse-papers.py
```

**Resume after interruption:**
```bash
python batch-igcse-papers.py --resume
```

## What It Does

1. **Navigates** to Pearson course materials page for each subject
2. **Expands** all sections to load PDFs
3. **Scrolls** page to trigger lazy-loading of all content
4. **Extracts** PDF links from page source
5. **Parses** filenames to identify:
   - Year and exam series (June/November/January)
   - Paper number (1, 2, etc.)
   - Tier (Foundation/Higher for some subjects)
   - Option (A, B, C for History, etc.)
   - Document type (QP, MS, ER)
6. **Groups** into complete sets (QP + MS + ER)
7. **Uploads** to database with proper metadata

## Output

### Console Output
```
[INFO] Starting Chrome...
[INFO] Scraping ALL 25 International GCSE subjects...

================================================================================
French (IG-French)
Code: 4fr1
================================================================================

[INFO] Waiting for page to load...
[INFO] Expanding sections...
[INFO] Scrolling to load all PDFs...
[INFO] Waiting for page to finish loading...
[INFO] Found 127 total PDF links on page
[OK] Parsed 45 papers
[OK] Grouped into 23 paper sets

[INFO] Uploading 23 paper sets to database...
[OK] Uploaded 23 paper sets successfully
```

### Database Records

Each paper set creates a record in `staging_aqa_exam_papers`:

```json
{
  "subject_code": "IG-French",
  "subject_name": "French",
  "qualification_type": "International GCSE",
  "exam_board": "Edexcel",
  "year": 2023,
  "exam_series": "June",
  "paper_number": 2,
  "tier": null,
  "option": null,
  "question_paper_url": "https://qualifications.pearson.com/.../4fr1-02-que-20230608.pdf",
  "mark_scheme_url": "https://qualifications.pearson.com/.../4fr1-02-rms-20230824.pdf",
  "examiner_report_url": "https://qualifications.pearson.com/.../4fr1-02-pef-20230824.pdf"
}
```

## Progress Tracking

The batch scraper creates checkpoints:

- **Log**: `batch-results/batch-papers-YYYYMMDD-HHMMSS.log`
- **Checkpoint**: `batch-results/checkpoint-papers.json`
- **Summary**: `batch-results/summary-papers-YYYYMMDD-HHMMSS.json`

If interrupted (Ctrl+C), run with `--resume` to continue from where you left off.

## Special Cases

### History Papers

History has multiple paper options (Paper 1A, 1B, 2A, 2B, etc.) for different historical periods/themes. The scraper correctly identifies and groups these.

Example:
```
4hi1-1a-que-20230608.pdf  → Paper 1 Option A
4hi1-1a-rms-20230824.pdf  → Paper 1 Option A Mark Scheme
4hi1-2b-que-20230608.pdf  → Paper 2 Option B
```

### Mathematics with Tiers

Mathematics papers may have Foundation (F) and Higher (H) tiers:

```
4ma1_1h_que_20220511.pdf  → Paper 1 Higher
4ma1_1f_que_20220511.pdf  → Paper 1 Foundation
```

## Requirements

- Python 3.7+
- Selenium WebDriver
- Chrome/Chromium
- BeautifulSoup4
- python-dotenv
- Database credentials in `.env`

## Troubleshooting

### No papers found
- Check the Pearson website URL is correct
- Verify the subject code matches actual paper codes
- Ensure sufficient scroll time for page to load all PDFs

### Database upload fails
- Verify `.env` file has correct Supabase credentials
- Check `upload_papers_to_staging.py` is in the correct path
- Ensure table `staging_aqa_exam_papers` exists

### Chrome crashes
- Add more memory: `--disable-dev-shm-usage`
- Reduce scroll iterations if page is small
- Check Chrome/ChromeDriver version compatibility

## Next Steps

After scraping, papers are available in the database for:
1. Display in the application
2. Linking to curriculum topics
3. Student practice and revision

---

**Last Updated**: November 2025  
**Maintained by**: Flash Curriculum Pipeline Team

