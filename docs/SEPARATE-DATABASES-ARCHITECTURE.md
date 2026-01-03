### Separate Exam Board Databases - Architecture Plan

## Executive Summary

**Decision:** Create isolated databases for each exam board (AQA, OCR, Edexcel) to safely develop and test scrapers without affecting the production FLASH app.

**Benefit:** Iterate on curriculum data quality without risk, integrate when ready.

---

## Database Structure

### Current Production (FLASH App)
- **Database:** Your main Supabase project
- **Tables:** users, flashcards, study_sessions, curriculum_topics (current)
- **Status:** Keep as-is, don't touch
- **Purpose:** Production app operation

### AQA Curriculum Database (New - Proof of Concept)
- **Schema Prefix:** `aqa_`
- **Tables:**
  - `aqa_subjects` (subject metadata)
  - `aqa_topics` (full 3-level hierarchy)
  - `aqa_components` (selection rules)
  - `aqa_constraints` (British+non-British, prohibited combos)
  - `aqa_exam_papers` (past papers, mark schemes)
  - `aqa_mark_scheme_insights` (AI-extracted patterns)
  - `aqa_examiner_report_insights` (common mistakes, advice)
  - `aqa_question_bank` (individual questions)

### Future: OCR, Edexcel, etc.
- Same pattern with `ocr_`, `edexcel_` prefixes
- Identical schema structure
- Independent development

---

## Integration Strategy (When Ready)

### Option 1: Database Views (Recommended)
```sql
-- Unified view combining all exam boards
CREATE VIEW curriculum_all_boards AS
SELECT 'AQA' as board, * FROM aqa_topics
UNION ALL
SELECT 'OCR' as board, * FROM ocr_topics
UNION ALL
SELECT 'Edexcel' as board, * FROM edexcel_topics;

-- App queries this view instead of individual tables
```

**Pros:** Clean, performant, single query interface  
**Cons:** Need to add UNION for each new board

### Option 2: API Layer
```typescript
// Curriculum API that abstracts database structure
async function getTopics(examBoard: string, subjectId: string) {
  const table = `${examBoard.toLowerCase()}_topics`;
  return await supabase.from(table).select('*').eq('subject_id', subjectId);
}
```

**Pros:** Maximum flexibility, can change DB structure anytime  
**Cons:** Extra code layer

### Option 3: Gradual Migration
```sql
-- When AQA data is perfect:
-- 1. Backup current topics
-- 2. Delete old AQA topics
-- 3. Copy from aqa_topics to curriculum_topics
-- 4. Repeat for each board
```

**Pros:** Eventually get to single unified table  
**Cons:** Risky if data isn't perfect

**Recommendation:** Start with Option 1 (views), migrate to Option 3 over time.

---

## Creating AQA Database (Today)

### Step 1: Create Schema
```sql
-- Run this in Supabase to create AQA tables
-- (Separate from main app tables)

CREATE TABLE aqa_subjects (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  subject_name TEXT NOT NULL,
  subject_code TEXT NOT NULL,
  qualification_type TEXT NOT NULL,
  specification_url TEXT,
  specification_pdf_url TEXT,
  total_guided_learning_hours INTEGER,
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(subject_code, qualification_type)
);

CREATE TABLE aqa_topics (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  subject_id UUID REFERENCES aqa_subjects(id),
  parent_topic_id UUID REFERENCES aqa_topics(id),
  
  topic_code TEXT NOT NULL,
  topic_name TEXT NOT NULL,
  topic_level INTEGER NOT NULL CHECK (topic_level >= 0 AND topic_level <= 3),
  
  description TEXT,
  component_code TEXT,
  chronological_period TEXT,
  geographical_region TEXT,
  key_themes JSONB,
  
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  
  UNIQUE(subject_id, topic_code)
);

CREATE TABLE aqa_components (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  subject_id UUID REFERENCES aqa_subjects(id),
  
  component_code TEXT NOT NULL,
  component_name TEXT NOT NULL,
  selection_type TEXT,  -- 'choose_one', 'choose_multiple', 'required_all'
  count_required INTEGER,
  total_available INTEGER,
  assessment_weight TEXT,
  
  UNIQUE(subject_id, component_code)
);

CREATE TABLE aqa_constraints (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  subject_id UUID REFERENCES aqa_subjects(id),
  
  constraint_type TEXT NOT NULL,
  description TEXT,
  constraint_rule JSONB,
  applies_to_components TEXT[]
);

CREATE INDEX idx_aqa_topics_subject ON aqa_topics(subject_id);
CREATE INDEX idx_aqa_topics_parent ON aqa_topics(parent_topic_id);
CREATE INDEX idx_aqa_topics_level ON aqa_topics(topic_level);
```

### Step 2: Update Scraper to Use AQA Tables
```python
# New uploader class
class AQADatabaseUploader:
    """Uploads to AQA-specific tables."""
    
    def upload_subject(self, subject_data):
        # Insert into aqa_subjects
        subject_id = supabase.table('aqa_subjects').upsert(...).execute()
        
        # Insert into aqa_topics with hierarchy
        self._upload_topics_hierarchical(subject_id, topics)
        
        # Insert into aqa_components
        self._upload_components(subject_id, components)
        
        # Insert into aqa_constraints  
        self._upload_constraints(subject_id, constraints)
```

### Step 3: Test with ONE Subject
```bash
python test_aqa_database.py --subject "Law"
```

Should create:
- 1 record in `aqa_subjects`
- 56 records in `aqa_topics` (with proper parent_topic_id!)
- 3 records in `aqa_components`
- 1 record in `aqa_constraints`

---

## Documentation Structure

```
flash-curriculum-pipeline/
├── docs/
│   ├── ARCHITECTURE.md                    ← Overall system design
│   ├── AQA-DATABASE-GUIDE.md             ← How AQA database works
│   ├── SCRAPER-DEVELOPMENT-GUIDE.md      ← How to build new scrapers
│   ├── INTEGRATION-PLAN.md               ← How to connect to app
│   └── MAINTENANCE-SCHEDULE.md           ← When to update
│
├── database/
│   ├── schemas/
│   │   ├── aqa_schema.sql
│   │   ├── ocr_schema.sql (future)
│   │   └── edexcel_schema.sql (future)
│   │
│   └── uploaders/
│       ├── aqa_uploader.py
│       └── base_uploader.py
│
└── scrapers/
    ├── aqa/
    │   ├── aqa_recursive_web_scraper.py  ← What we built
    │   └── aqa_assessment_scraper.py
    │
    └── ocr/ (future)
```

---

## Maintenance Plan

### Quarterly Updates (Every 3 Months)
**When:** September, December, March, June  
**Why:** Exam boards update specifications  
**What:**
1. Run scraper for each board
2. Compare with existing data (what changed?)
3. Update databases with new content
4. Notify users of curriculum changes

### Annual Major Update (September)
**When:** Start of academic year  
**Why:** New specifications released  
**What:**
1. Full re-scrape of all boards
2. Validate all 68+ subjects
3. Update assessment resources (new past papers)
4. Re-run AI analysis on new papers

### Ad-hoc Updates
**When:** User reports missing/incorrect content  
**What:**
1. Fix specific subject
2. Document the issue
3. Improve scraper if needed

---

## Future App Integration

### Phase 1: Read-Only (Safest)
```typescript
// App queries AQA database for curriculum info
const topics = await supabase
  .from('aqa_topics')
  .select('*')
  .eq('subject_id', subjectId);

// But continues to use main database for user data
```

### Phase 2: Hybrid (Testing)
```typescript
// Use AQA for new users (beta testers)
if (user.isBetaTester) {
  topics = await getFromAQADatabase();
} else {
  topics = await getFromMainDatabase();
}
```

### Phase 3: Full Migration (When Perfect)
```sql
-- Migrate all curriculum data to unified structure
-- Drop old tables
-- Everyone uses new high-quality data
```

---

## Cost Tracking

### One-Time Setup Costs
- AQA scraping (68 subjects): $10-15
- OCR scraping (50 subjects): $8-12
- Edexcel scraping (50 subjects): $8-12
- **Total**: ~$25-40

### Ongoing Costs (Annual)
- Quarterly updates: $5-8 per quarter × 4 = $20-30/year
- Assessment analysis: $20-30/year (new papers only)
- **Total**: ~$40-60/year

---

## Risk Mitigation

### Data Quality Issues
**Risk:** Scraper extracts wrong content  
**Mitigation:** 
- Staging databases
- Manual spot-checks
- User feedback loop
- Easy rollback

### Scraper Failures
**Risk:** AQA website changes structure  
**Mitigation:**
- Version scrapers
- Fallback to PDF extraction
- Monitoring alerts
- Historical data backups

### Integration Bugs
**Risk:** App breaks when switching databases  
**Mitigation:**
- Gradual rollout (beta testers first)
- Feature flags
- Schema compatibility tests
- Rollback plan

---

## Next Steps (Today)

1. **Create AQA schema SQL** (20 min)
2. **Update uploader for AQA tables** (30 min)
3. **Test with Law** (10 min)
4. **Document and commit** (10 min)
5. **Return to app development!**

**Total:** ~70 minutes to create solid foundation, then focus on app!

---

## Documentation Checklist

Before returning to app, create:

- [ ] AQA schema SQL file
- [ ] AQA uploader Python class
- [ ] Test script for single subject
- [ ] README explaining the system
- [ ] Integration guide (for future)
- [ ] Commit to GitHub

**Want me to create these files now?** Then you can:
- Run one test scrape into AQA database
- Verify it works
- Commit everything
- Focus on app for weeks/months
- Come back to scraping when app is stable!

This is a **much better plan** than trying to perfect everything now! 🎯





















