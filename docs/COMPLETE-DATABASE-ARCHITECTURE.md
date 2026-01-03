# Complete Database Architecture - Current vs Proposed

## Current Production Database (What Exists Now)

```
SUPABASE - Production Database (FLASH App)
│
├─ USER MANAGEMENT
│  ├─ users (auth.users + profile data)
│  ├─ user_subjects (which subjects user selected)
│  ├─ user_topics (which topics user selected)
│  └─ user_stats (streak, XP, etc.)
│
├─ FLASHCARD SYSTEM
│  ├─ flashcards (user's cards)
│  ├─ card_reviews (Leitner box system)
│  ├─ study_sessions (session tracking)
│  └─ daily_study_cards (today's cards)
│
├─ CURRICULUM DATA (What Yesterday Tried to Improve)
│  ├─ exam_boards
│  │  ├─ id, code ('AQA', 'OCR', 'Edexcel')
│  │  └─ 6 boards total
│  │
│  ├─ qualification_types  
│  │  ├─ id, code ('A_LEVEL', 'GCSE')
│  │  └─ 5 types total
│  │
│  ├─ exam_board_subjects
│  │  ├─ id, exam_board_id, qualification_type_id
│  │  ├─ subject_name, subject_code
│  │  └─ ~80 AQA subjects (but includes duplicates from various imports)
│  │
│  └─ curriculum_topics ⚠️ PROBLEMATIC!
│     ├─ id, exam_board_subject_id
│     ├─ topic_code, topic_name, topic_level
│     ├─ parent_topic_id (hierarchy)
│     ├─ component_code, chronological_period, geographical_region
│     └─ ~12,000 topics total
│         - 5,191 from June (basic, no metadata)
│         - 7,000 from yesterday (duplicates, missing hierarchy)
│         - ISSUES: Massive duplicates, broken parent relationships
│
├─ ENHANCED CURRICULUM (Yesterday's Work)
│  ├─ specification_metadata
│  │  ├─ 67 AQA subjects with metadata
│  │  └─ Links to components & constraints
│  │
│  ├─ spec_components
│  │  ├─ 183 components (after cleanup)
│  │  └─ Selection rules (choose_one, required_all)
│  │
│  └─ selection_constraints
│     ├─ 150 constraints (after cleanup)
│     └─ British+non-British, prohibited combos
│
└─ ASSESSMENT RESOURCES (Partially Built)
   ├─ exam_papers (50 papers from 9 subjects)
   ├─ mark_scheme_insights (6 from Accounting)
   ├─ examiner_report_insights (6 from Accounting)
   └─ question_bank (24 questions from Accounting)
```

### Current Issues:
❌ curriculum_topics has 12,000 records but ~6,500 should be unique  
❌ Parent-child relationships broken for most topics  
❌ Duplicates from multiple scraper runs  
❌ Can't add unique constraint due to existing duplicates  
❌ Risky to clean without breaking app  

---

## Proposed Architecture: Separate AQA Database

```
SUPABASE - Production Database
│
├─ [Everything above stays untouched]
│
├─ AQA CURRICULUM DATABASE (NEW - Isolated) 
│  │
│  ├─ aqa_subjects
│  │  ├─ id UUID PRIMARY KEY
│  │  ├─ subject_name, subject_code, qualification_type
│  │  ├─ specification_url, specification_pdf_url
│  │  ├─ total_guided_learning_hours
│  │  └─ UNIQUE(subject_code, qualification_type) ← No duplicates!
│  │
│  ├─ aqa_topics
│  │  ├─ id UUID PRIMARY KEY
│  │  ├─ subject_id → aqa_subjects(id)
│  │  ├─ parent_topic_id → aqa_topics(id) ← Proper hierarchy!
│  │  ├─ topic_code, topic_name, topic_level (0, 1, 2, 3)
│  │  ├─ description, component_code
│  │  ├─ chronological_period, geographical_region
│  │  └─ UNIQUE(subject_id, topic_code) ← Guaranteed unique!
│  │
│  ├─ aqa_components
│  │  ├─ id, subject_id
│  │  ├─ component_code, component_name
│  │  ├─ selection_type, count_required, total_available
│  │  └─ UNIQUE(subject_id, component_code)
│  │
│  ├─ aqa_constraints
│  │  ├─ id, subject_id
│  │  ├─ constraint_type, description, constraint_rule (JSONB)
│  │  └─ applies_to_components
│  │
│  ├─ aqa_exam_papers
│  │  ├─ id, subject_id, year, exam_series, paper_number
│  │  ├─ question_paper_url, mark_scheme_url, examiner_report_url
│  │  └─ UNIQUE(subject_id, year, exam_series, paper_number)
│  │
│  ├─ aqa_mark_scheme_insights
│  │  ├─ id, exam_paper_id
│  │  └─ question_types, key_command_words, marking_criteria
│  │
│  ├─ aqa_examiner_report_insights
│  │  ├─ id, exam_paper_id
│  │  └─ common_mistakes, strong_answers, areas_of_improvement
│  │
│  └─ aqa_question_bank
│     ├─ id, exam_paper_id
│     └─ question_number, question_text, marks, mark_scheme_points
│
└─ OCR CURRICULUM DATABASE (Future)
   └─ ocr_subjects, ocr_topics, ocr_components, etc.
```

### Benefits of Separation:
✅ **Clean slate** - No duplicate baggage  
✅ **Proper constraints** - Can enforce uniqueness from day 1  
✅ **Safe testing** - Can't break production app  
✅ **Easy validation** - Compare quality before switching  
✅ **Rollback simple** - Just drop aqa_* tables if needed  

---

## Comparison: Current vs Proposed

| Aspect | Current (curriculum_topics) | Proposed (aqa_topics) |
|--------|----------------------------|----------------------|
| **Total records** | 12,191 | ~2,000 (unique only) |
| **Duplicates** | ~6,000+ | 0 (enforced by constraint) |
| **Parent relationships** | Broken for most | Working for all |
| **Level 0 topics** | 1,870 | ~68 (one per subject) |
| **Level 1 topics** | 5,541 | ~1,500 |
| **Level 2 topics** | 1,099 | ~400 |
| **Level 3 topics** | 3,681 | ~100 |
| **Has component_code** | 52 | All (where applicable) |
| **Has periods/regions** | 285 | All (for History) |
| **Data quality** | Mixed (old + new) | Consistent (all new) |
| **Can add constraints** | ❌ No (duplicates) | ✅ Yes |
| **Safe to update** | ❌ No (might break app) | ✅ Yes |

---

## Integration Roadmap

### Phase 1: Build (This Week)
- Create AQA schema
- Build AQA-specific scraper & uploader
- Test with 5 subjects (Law, Psychology, PE, Biology, History)
- Validate data quality

### Phase 2: App Beta Testing (Next 2 Weeks)
- Continue using CURRENT database for app
- AQA database sits unused
- Focus on app features & UX
- Get user feedback

### Phase 3: Data Validation (Week 4)
- Compare AQA database vs current topics
- Spot-check 10-20 subjects manually
- Verify hierarchy works correctly
- Test app integration with AQA data

### Phase 4: Gradual Migration (Month 2)
- Beta testers use AQA data
- Monitor for issues
- Fix any problems in isolated AQA database
- Don't touch production

### Phase 5: Full Rollout (Month 3+)
- When confident, create unified view:
```sql
CREATE VIEW curriculum_topics_v2 AS
SELECT * FROM aqa_topics
UNION ALL  
SELECT * FROM ocr_topics;
```
- Update app to use new view
- Deprecate old curriculum_topics table

---

## Decision Point

**Option A: Full Separation (Recommended)**
- Create aqa_*, ocr_*, edexcel_* tables
- Keep completely isolated
- Integrate via views when ready

**Option B: Namespace Within Current DB**
- Add `source_board` column to current tables
- Partition data by board
- Cleaner but harder to manage duplicates

**Option C: Hybrid**
- Use separate AQA database in different Supabase project
- Connect via API when ready
- Maximum isolation

**Recommendation:** Option A - separate tables with `aqa_` prefix in SAME Supabase project.

---

## What to Build Today

**Deliverables:**
1. `CREATE-AQA-SCHEMA.sql` - Creates all aqa_* tables
2. `aqa_uploader.py` - Uploads to AQA tables with proper hierarchy
3. `test_aqa_database.py` - Tests with Law
4. `AQA-DATABASE-README.md` - How to use it
5. Commit everything to GitHub

**Time:** 60-90 minutes  
**Result:** Working AQA database ready for future use

**Ready to start?**




















