# 🌙 Overnight International GCSE Batch Scraper Guide

## What It Does

Automatically scrapes **all 37 International GCSE subjects** using GPT-4 AI with:
- ✅ Smart structure detection (reads "Qualification at a glance")
- ✅ Handles History/RE with multiple optional routes
- ✅ Contextual vocabulary for language subjects (Tamil, Arabic, Chinese, etc.)
- ✅ Progress tracking and auto-save checkpoints
- ✅ Automatic retries on failures
- ✅ Detailed logging

## Estimated Stats

| Metric | Estimate |
|--------|----------|
| **Subjects** | 37 International GCSE |
| **Time** | 2-4 hours |
| **Cost** | $7-10 total |
| **Topics** | ~5,000-7,000 total |
| **Avg per subject** | ~150-200 topics |

## ⚡ Quick Start

### 1. Start the Batch

```bash
cd "C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\scrapers\Edexcel\International"

python overnight-igcse-batch.py
```

It will ask for confirmation, then run unattended.

### 2. Let It Run Overnight

The script will:
- Process subjects one by one
- Save progress after each subject
- Log everything to `batch-results/overnight-igcse-TIMESTAMP.log`
- Create checkpoint file for resume capability

### 3. If Interrupted (Ctrl+C)

Progress is automatically saved! Just resume:

```bash
python overnight-igcse-batch.py --resume
```

## 📊 Monitoring Progress

### Check Logs (Real-time)
```bash
# View latest log
cd batch-results
tail -f overnight-igcse-*.log

# Or on Windows PowerShell:
Get-Content overnight-igcse-*.log -Wait -Tail 20
```

### Check Checkpoint
```bash
# See what's been completed
cat batch-results/checkpoint-igcse.json
```

### View in Database
Open your data viewer at `data-viewer-v2.html`:
- Select: **Edexcel** + **International GCSE**
- Watch subjects appear as they're scraped!

## 🎯 What Gets Scraped

### Regular Subjects (Biology, Chemistry, Physics, Math, etc.)
- Paper 1, Paper 2 structure
- All topics per paper
- Practical investigations
- ~150-250 topics each

### Language Subjects (Tamil, Arabic, French, Spanish, etc.)
- Themes and topics
- **Smart vocabulary mapping** - native script distributed to relevant topics
- Grammar contextually integrated
- ~50-150 topics each

### History
- ALL optional time periods (Medieval, Early Modern, Modern, etc.)
- Each period with depth studies
- Key events, figures, causes, consequences
- ~300-500 topics (large!)

### Religious Studies  
- ALL religions (Buddhism, Christianity, Hinduism, Islam, Judaism, Sikhism)
- Beliefs, practices, texts for each religion
- ~200-400 topics (large!)

### Geography
- All topics with case studies
- Regional examples
- ~100-200 topics

## 📁 Output Files

All saved to `batch-results/`:

- `overnight-igcse-TIMESTAMP.log` - Detailed execution log
- `checkpoint-igcse.json` - Progress checkpoint (for resume)
- `summary-igcse-TIMESTAMP.json` - Final summary with all results
- `../adobe-ai-output/[SUBJECT]-gpt4-output.txt` - Raw AI output for each subject

## ⚠️ Troubleshooting

### Subject Failed
Check the log file for the specific error. Common issues:
- **PDF download failed** - Network issue, retry
- **GPT-4 timeout** - PDF too large, may need manual handling
- **Parsing failed** - AI output format unexpected

Failed subjects are tracked in checkpoint and can be re-run individually:
```bash
python ai-powered-scraper-openai.py --subject IG-History
```

### Want to Review Before Full Batch?

Test a few subjects first:
```bash
# Test sciences
python ai-powered-scraper-openai.py --subject IG-Physics

# Test languages  
python ai-powered-scraper-openai.py --subject IG-French

# Test History (big one!)
python ai-powered-scraper-openai.py --subject IG-History

# Test Religious Studies (big one!)
python ai-powered-scraper-openai.py --subject IG-ReligiousStudies
```

Then review in data viewer before running full batch.

## 🔄 After Batch Completes

### 1. Review Summary
```bash
cat batch-results/summary-igcse-TIMESTAMP.json
```

Shows:
- Success/failure counts
- Total topics extracted
- Time taken
- Any failed subjects

### 2. Check Failed Subjects

If any failed, re-run them individually or adjust and retry.

### 3. Verify in Data Viewer

Open `data-viewer-v2.html`:
- Select: **Edexcel** + **International GCSE**
- Review subjects for quality
- Check Tamil has native vocabulary integrated
- Check History has all periods
- Check RE has all religions

### 4. Next: International A Level

Once IGCSE is done, run A Level batch:
```bash
# Coming soon: overnight-ial-batch.py
python ai-powered-scraper-openai.py --all-ial
```

Or I can create a similar batch script for A Level (21 subjects, ~$4-5, ~1-2 hours).

## 💾 Ready for Git Commit

After successful batch, commit everything:
```bash
git add scrapers/Edexcel/International/
git commit -m "Complete International GCSE AI scraping

- Scraped all 37 International GCSE subjects using GPT-4
- Smart vocabulary mapping for language subjects
- All History periods and RE religions included
- Total: ~5,000-7,000 topics extracted
- Cost: ~$7-10, Time: ~2-4 hours"

git push
```

---

**Ready to start the overnight batch?** 🚀

