# AQA GCSE Overnight Scraper

## 🌙 Run Before Bed

### Topics (Node.js):
```bash
cd "C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\scrapers\AQA\GCSE"
node run-all-gcse-topics.js > gcse-topics-log.txt 2>&1
```

### Papers (Python):
```bash
cd "C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\scrapers\AQA\GCSE"
python run-all-gcse-papers.py > gcse-papers-log.txt 2>&1
```

### Both in Sequence:
```bash
cd "C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\scrapers\AQA\GCSE"
node run-all-gcse-topics.js && python run-all-gcse-papers.py
```

## 📊 Check Results in Morning

1. Open `data-viewer.html` in browser
2. Select "GCSE" from Qualification filter
3. Review all 41 GCSE subjects
4. Check topic counts are reasonable
5. Verify papers are present

## 📝 Expected Results

- **~41 GCSE subjects**
- **~2,000-4,000 topics** (GCSEs are simpler than A-Levels)
- **~400-600 paper sets**
- **Est. runtime:** 2-3 hours for topics, 4-5 hours for papers

## ⚠️ Notes

- Firecrawl may hit rate limits - some pages might fail
- Re-run individual subjects if needed
- Check log files for errors
- Some low-volume subjects may have 0 papers (normal)

## 🔧 If Issues

Individual subject scrapers are in:
- `../A-Level/topics/crawl-aqa-{subject}.js`
- `../A-Level/papers/scrape-{subject}-papers.py`

Adapt these for GCSE by changing:
- URL: `/a-level/` → `/gcse/`
- Qualification: `'A-Level'` → `'GCSE'`
- Subject code: (use GCSE code from aqa-gcse-subjects.json)

