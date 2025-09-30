# FLASH Curriculum Pipeline v2

Intelligent curriculum content scraper for FLASH educational app. Extracts comprehensive topic data from UK and international exam boards with AI-assisted analysis.

## Features

- 🌍 **Comprehensive Coverage**: UK exam boards (AQA, Edexcel, OCR, WJEC, SQA, CCEA) + International (Cambridge, IB)
- 🤖 **AI-Enhanced Extraction**: Uses Claude & Gemini to extract specification structure, constraints, and detailed topics
- 📊 **Rich Metadata**: Captures component structure, selection rules, assessment context
- 🔄 **Automated Updates**: GitHub Actions runs every 6 months
- 💾 **Direct Supabase Integration**: Batch uploads with deduplication
- 🎯 **Context-Aware**: Understands how students actually select and study topics

## What Makes This v2

**v1 (Node.js - archived):** Simple AI topic generation  
**v2 (Python):** Comprehensive scraping + enhanced AI extraction with specification metadata

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Test with single subject
python scripts/test_single_subject.py --board AQA --subject History --qualification a-level

# Run full pipeline
python pipeline.py
```

## Architecture

```
Scrapers → AI Extractors → Processors → Supabase
   ↓           ↓              ↓            ↓
  PDFs    Metadata        Normalize    Batch
  HTML    Constraints     Dedupe       Upsert
         Topics          Validate
```

## What Gets Extracted

For each subject:
1. **Specification Metadata** - Overview, assessment structure
2. **Component Structure** - How course is organized (e.g., Component 1, 2, 3)
3. **Selection Constraints** - Rules students must follow
4. **Topic Options** - Choosable topics with metadata (periods, regions, themes)
5. **Detailed Subtopics** - Granular content for each option
6. **Assessment Context** - Question types, mark schemes, focus areas
7. **Subject Vocabulary** - Key terms and concepts

## Example: History A-Level

Extracts structure showing students must:
- Choose 1 from Component 1 (11 Breadth Studies)
- Choose 1 from Component 2 (20 Depth Studies)
- Include 1 British + 1 non-British option
- Avoid prohibited combinations
- Cover 200+ year chronological span

## Timeline

- **Weeks 1-2:** UK boards with Supabase integration
- **Weeks 3-4:** Automation & quality assurance
- **Weeks 5-8:** International expansion (Cambridge, IB, Edexcel International)

## Documentation

- `docs/ARCHITECTURE.md` - System design
- `docs/SCRAPER_GUIDE.md` - How scrapers work
- `docs/AI_PROMPTS.md` - Extraction strategies
- `ENHANCED-SCRAPER-DESIGN.md` - Specification constraints approach

## License

Copyright © 2025 4Sight Education Ltd. All rights reserved.

---

**Previous Version:** See `archive/nodejs-version` branch for the original Node.js implementation