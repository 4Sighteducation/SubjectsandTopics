# FLASH Curriculum Pipeline - Complete Implementation Plan
**Date:** September 30, 2025  
**Status:** Production-Ready Strategy

---

## Executive Summary

This document outlines the complete strategy to make FLASH scrapers operational, process all subjects (UK + International), and implement subject pathway/constraint UI in the app.

### Current Status ✅

**What's Working:**
- ✅ Database schema complete (specification, constraints, assessment resources)
- ✅ Single-subject scraping works (tested with History A-Level)
- ✅ AI extraction working (metadata, components, constraints, topics)
- ✅ Supabase integration functional
- ✅ Historical data exists in database

**What's Not Working:**
- ❌ Batch automation for all 74 AQA subjects
- ❌ International scrapers (Cambridge, IB) not yet created
- ❌ Assessment resources scraper (past papers, mark schemes) not built
- ❌ Subject pathway UI not implemented in FLASH app

**What We Just Fixed:**
- ✅ Created `batch_processor.py` - robust batch processing with resume capability
- ✅ Created `check_existing_data.py` - audit tool to see what's in Supabase
- ✅ Created `cambridge_scraper.py` - Cambridge IGCSE/A-Level scraper
- ✅ Created `RUN-BATCH-AQA.bat` - easy-to-use batch file

---

## Phase 1: Audit & Clean Existing Data (TODAY)

### Step 1: Check What Data Already Exists

```bash
cd "C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline"
python check_existing_data.py
```

This will:
- Count all records in each table
- Show sample data
- Identify gaps
- Generate HTML report with recommendations
- **Opens automatically in browser**

### Step 2: Review Audit Report

Look for:
1. **How many topics already scraped?** (curriculum_topics table)
2. **Which exam boards have data?** (AQA, OCR, etc.)
3. **Any specification metadata?** (specification_metadata table)
4. **Any assessment resources?** (exam_papers table - likely empty)

### Step 3: Decide on Strategy

**Option A: Start Fresh**
- Clear old data
- Run batch processor for all 74 AQA subjects
- Clean, consistent data

**Option B: Keep & Enhance**
- Keep existing topics
- Only scrape subjects missing specification metadata
- Add constraints/components to existing subjects

**Recommendation:** Start with Option B (safer), switch to A only if data quality is poor.

---

## Phase 2: Complete AQA Scraping (THIS WEEK)

### Run Batch Processor

**Test First** (recommended):
```bash
cd "C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline"
python batch_processor.py --test
```

This processes only 3 subjects to verify everything works.

**Full Run**:
```bash
# Option 1: Use the batch file
RUN-BATCH-AQA.bat

# Option 2: Run directly
python batch_processor.py
```

**What It Does:**
- Processes all 74 AQA subjects (A-Level + GCSE)
- For each subject:
  1. Finds specification PDF
  2. Downloads it
  3. Extracts with AI (metadata, components, constraints, topics)
  4. Uploads to Supabase
- **Saves progress** - can resume if interrupted
- **Generates HTML report** with results
- **Takes 2-4 hours** for all subjects

### Monitor Progress

The batch processor:
- ✅ Logs everything to `data/logs/batch_YYYYMMDD_HHMMSS.log`
- ✅ Saves state to `data/state/batch_state_YYYYMMDD_HHMMSS.json`
- ✅ Can be stopped (Ctrl+C) and resumed

### After Completion

Check the HTML report that opens automatically. It shows:
- ✅ Successfully completed subjects
- ⚠️ Partially completed (some data but had issues)
- ❌ Failed subjects

For failed subjects, check the log file and re-run individually:
```bash
cd "C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline"
python -m scrapers.uk.aqa_scraper_enhanced --subject "History" --exam-type "A-Level"
```

---

## Phase 3: International Scrapers (NEXT WEEK)

### Cambridge International (Priority 1)

**Test with single subject**:
```bash
python -m scrapers.international.cambridge_scraper --subject "Mathematics" --qual "IGCSE"
```

**List all available subjects**:
```bash
python -m scrapers.international.cambridge_scraper --list
```

**Run all Cambridge subjects**:
Create `batch_processor_cambridge.py` (similar to AQA batch processor):
```bash
python batch_processor_cambridge.py
```

**Expected Output:**
- ~17 IGCSE subjects (most popular)
- ~14 A-Level subjects (most popular)
- Total: ~20,000-25,000 topics

### International Baccalaureate (Priority 2)

**Challenge:** Some IB content requires login/subscription.

**Strategy:**
1. Scrape publicly available subject briefs
2. Extract what we can with AI
3. For restricted content, either:
   - Partner with IB schools for access
   - Use fallback topic structures
   - Focus on publicly available subjects only

**Create IB scraper** (similar to Cambridge):
```python
# File: scrapers/international/ib_scraper.py
# Similar structure to cambridge_scraper.py
```

**Expected Output:**
- ~25-30 subjects (partial coverage)
- ~5,000-8,000 topics
- Documented limitations

### Other International Boards

**Edexcel International** (Quick win - similar to UK Edexcel):
```bash
# Just adapt existing edexcel_scraper.py
python -m scrapers.international.edexcel_international_scraper
```

**Future expansions:**
- AP (Advanced Placement) - USA
- Singapore-Cambridge GCE
- Hong Kong HKDSE

---

## Phase 4: Assessment Resources Scraper (2 WEEKS)

### What We Need to Scrape

For each subject:
1. **Past Papers** (last 3 years recommended)
   - Question papers (PDFs)
   - Mark schemes (PDFs)
   - Examiner reports (PDFs)

2. **AI Extraction** from these documents:
   - Common question types
   - Marking criteria patterns
   - Common mistakes from examiner reports
   - Individual questions for AI training

### Implementation

**Create assessment resources scraper**:
```python
# File: scrapers/assessment_resources_scraper.py

class AssessmentResourcesScraper:
    """Scrape past papers, mark schemes, examiner reports."""
    
    def scrape_papers_for_subject(self, exam_board, subject, qualification, years=[2022, 2023, 2024]):
        """
        For AQA History A-Level:
        1. Navigate to: https://www.aqa.org.uk/subjects/history/a-level/history-7042/assessment-resources
        2. Filter by year (2024, 2023, 2022)
        3. Find PDFs for:
           - Question papers (Component 1, 2, 3)
           - Mark schemes
           - Examiner reports
        4. Download to: data/assessment_resources/AQA/History_A-Level/2024/
        5. Extract text with PyPDF2/pdfplumber
        6. Upload metadata to exam_papers table
        """
        pass
    
    def extract_mark_scheme_insights(self, pdf_path):
        """
        Use AI to analyze mark scheme:
        - What question types? (essay, source analysis, etc.)
        - Common command words? (evaluate, explain, etc.)
        - How are marks allocated?
        - What do examiners look for?
        
        Upload to mark_scheme_insights table.
        """
        pass
    
    def extract_examiner_report_insights(self, pdf_path):
        """
        Use AI to analyze examiner report:
        - What mistakes did students make?
        - What did good answers include?
        - Performance statistics?
        - Examiner advice?
        
        Upload to examiner_report_insights table.
        """
        pass
```

**Cost Estimate:**
- Papers download: Free (just bandwidth)
- AI extraction: ~$0.10-0.15 per paper
- Per subject (3 years, 3 papers/year = 9 documents): ~$1-1.50
- All 74 AQA subjects: ~$75-110
- **Total for UK + International: ~$200-300**

### Assessment Resource URLs

**AQA Pattern:**
```
Base: https://www.aqa.org.uk/subjects/{subject}/{qual}/{subject}-{code}/assessment-resources

Example:
https://www.aqa.org.uk/subjects/history/a-level/history-7042/assessment-resources

PDFs are on:
https://filestore.aqa.org.uk/resources/history/...
```

**Cambridge Pattern:**
```
Base: https://www.cambridgeinternational.org/programmes-and-qualifications/{qual}-{subject}-{code}/

Then look for "Past papers" or "Specimen papers" section
```

**Implementation Timeline:**
- Week 1: Build scraper for AQA
- Week 2: Test with 5 subjects, extract insights with AI
- Week 3: Expand to all AQA subjects
- Week 4: Add Cambridge & other boards

---

## Phase 5: Subject Pathways UI in FLASH App (2-3 WEEKS)

### What Are Subject Pathways?

For subjects like History, students must choose specific options/eras:
- **Component 1:** Choose 1 from 11 options (1A, 1B, 1C, ...)
- **Component 2:** Choose 1 from 20 options (2A, 2B, 2C, ...)

**Constraints:**
- Must choose one British and one non-British option
- Cannot choose certain combinations (e.g., 1C + 2A prohibited)

**Similar patterns in:**
- English Literature (must choose specific texts)
- Psychology (must choose research methods + optional topics)
- Combined Science (must choose which topics)

### Current App Flow (Simplified)

```typescript
// User picks subject
user.subjects.push({ 
  exam_board: 'AQA', 
  subject: 'History', 
  qualification: 'A-Level' 
});

// App shows all topics for that subject
const topics = await supabase
  .from('curriculum_topics')
  .select('*')
  .eq('exam_board_subject_id', subjectId);

// User selects any topics they want
// Problem: No validation of constraints!
```

### Enhanced App Flow (With Pathways)

```typescript
// 1. User picks subject
const subject = { exam_board: 'AQA', subject: 'History', qualification: 'A-Level' };

// 2. Check if subject has selection constraints
const spec = await supabase
  .from('specification_metadata')
  .select(`
    *,
    components:spec_components(*),
    constraints:selection_constraints(*)
  `)
  .eq('exam_board', 'AQA')
  .eq('subject_name', 'History')
  .eq('qualification_type', 'a_level')
  .single();

// 3. If has constraints, show guided selection
if (spec.components.some(c => c.selection_type !== 'required_all')) {
  // Show pathway selection UI
  await showPathwaySelection(spec);
} else {
  // All required - show all topics
  await showAllTopics(subjectId);
}
```

### Pathway Selection UI (Example)

```tsx
// Screen: PathwaySelectionScreen.tsx

function PathwaySelectionScreen({ subject, specification }) {
  const [selectedOptions, setSelectedOptions] = useState({});
  const [errors, setErrors] = useState([]);

  // Component 1: Choose 1 from 11
  const component1Options = specification.components.find(c => c.component_code === 'C1');
  
  return (
    <View>
      <Text style={styles.title}>Choose Your Study Options</Text>
      <Text style={styles.subtitle}>
        History A-Level requires you to select specific historical periods.
      </Text>

      {/* Component 1 Selection */}
      <View style={styles.component}>
        <Text style={styles.componentTitle}>
          Component 1: {component1Options.component_name}
        </Text>
        <Text style={styles.rule}>
          Choose {component1Options.count_required} from {component1Options.total_available}
        </Text>

        <ScrollView>
          {component1Topics.map(topic => (
            <TouchableOpacity
              key={topic.id}
              style={[
                styles.optionCard,
                selectedOptions.c1 === topic.id && styles.optionSelected
              ]}
              onPress={() => selectOption('c1', topic.id)}
            >
              <Text style={styles.optionCode}>{topic.topic_code}</Text>
              <Text style={styles.optionTitle}>{topic.topic_name}</Text>
              <Text style={styles.optionPeriod}>{topic.chronological_period}</Text>
              <Text style={styles.optionRegion}>
                Region: {topic.geographical_region}
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      </View>

      {/* Component 2 Selection */}
      {/* ... similar structure ... */}

      {/* Constraint Validation */}
      {errors.length > 0 && (
        <View style={styles.errors}>
          {errors.map((error, i) => (
            <Text key={i} style={styles.error}>{error}</Text>
          ))}
        </View>
      )}

      {/* Confirm Button */}
      <TouchableOpacity 
        style={styles.confirmButton}
        onPress={validateAndSave}
        disabled={!isValid()}
      >
        <Text style={styles.confirmText}>Confirm Selections</Text>
      </TouchableOpacity>
    </View>
  );
}

function validateSelections(selectedOptions, constraints) {
  const errors = [];
  
  // Check geographic diversity
  const diversityConstraint = constraints.find(c => c.constraint_type === 'geographic_diversity');
  if (diversityConstraint) {
    const topics = getSelectedTopics(selectedOptions);
    const hasBritish = topics.some(t => t.geographical_region === 'British');
    const hasNonBritish = topics.some(t => t.geographical_region !== 'British');
    
    if (!hasBritish || !hasNonBritish) {
      errors.push('You must choose one British and one non-British option');
    }
  }
  
  // Check prohibited combinations
  const prohibitedConstraint = constraints.find(c => c.constraint_type === 'prohibited_combination');
  if (prohibitedConstraint) {
    const prohibited = prohibitedConstraint.constraint_rule.prohibited_pairs;
    const selected = Object.values(selectedOptions);
    
    for (const [code1, code2] of prohibited) {
      if (selected.includes(code1) && selected.includes(code2)) {
        errors.push(`Cannot choose ${code1} and ${code2} together`);
      }
    }
  }
  
  return errors;
}
```

### Implementation Steps

**Week 1: Backend Logic**
1. Create TypeScript types for specifications:
   ```typescript
   // types/curriculum.ts
   export interface SpecificationMetadata {
     id: string;
     exam_board: string;
     qualification_type: string;
     subject_name: string;
     components: ComponentRule[];
     constraints: SelectionConstraint[];
   }
   
   export interface ComponentRule {
     component_code: string;
     component_name: string;
     selection_type: 'choose_one' | 'choose_multiple' | 'required_all';
     count_required: number;
     total_available: number;
   }
   
   export interface SelectionConstraint {
     constraint_type: string;
     constraint_rule: any;
     description: string;
   }
   ```

2. Create validation utility:
   ```typescript
   // utils/pathwayValidation.ts
   export class PathwayValidator {
     validateSelection(
       selectedTopics: string[],
       constraints: SelectionConstraint[]
     ): ValidationResult {
       // Implementation
     }
   }
   ```

**Week 2: UI Components**
1. Create `PathwaySelectionScreen.tsx`
2. Create `OptionCard.tsx` component
3. Create `ConstraintInfo.tsx` component (shows rules)
4. Add to navigation flow

**Week 3: Integration & Testing**
1. Integrate with existing subject selection flow
2. Test with History (complex constraints)
3. Test with Mathematics (no constraints - all required)
4. Test with English Literature (text selection)
5. User testing with beta testers

### Fallback for Missing Specifications

```typescript
// If no specification metadata exists, fall back to old behavior
if (!specification || specification.components.length === 0) {
  // Show all topics, let user select freely
  return <SimpleTopicSelection subjectId={subjectId} />;
}
```

---

## Phase 6: GitHub Commit & Push

After each phase, commit changes:

```bash
cd "C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline"

# Add all changes
git add .

# Commit with descriptive message
git commit -m "Add batch processor, Cambridge scraper, and data audit tool"

# Push to GitHub
git push origin main
```

**Recommended commits:**
1. "Add robust batch processor for all AQA subjects"
2. "Add Cambridge International scraper (IGCSE + A-Level)"
3. "Add data audit tool to check existing Supabase data"
4. "Add assessment resources scraper (past papers, mark schemes)"
5. "Add subject pathway UI to FLASH app"

---

## Complete Timeline

| Phase | Task | Duration | Output |
|-------|------|----------|--------|
| 1 | Audit existing data | 1 hour | HTML report, strategy decision |
| 2 | Run AQA batch processor | 2-4 hours | 74 subjects scraped |
| 3 | International scrapers | 1 week | Cambridge, IB, Edexcel Intl |
| 4 | Assessment resources scraper | 2 weeks | Past papers, mark schemes, insights |
| 5 | Subject pathways UI | 2-3 weeks | Enhanced app with constraint validation |
| **Total** | | **4-5 weeks** | **Complete system** |

---

## Cost Breakdown

| Item | Cost | Notes |
|------|------|-------|
| AQA scraping (74 subjects) | $7-12 | AI extraction for metadata |
| Cambridge scraping (~30 subjects) | $3-5 | Similar AI extraction |
| IB scraping (~25 subjects) | $2-4 | Partial coverage |
| Assessment resources (150 subjects × 9 docs) | $200-300 | Mark schemes, examiner reports analysis |
| **Total** | **$212-321** | One-time cost |
| **Ongoing** (6-month updates) | $50-75 | Update specifications |

---

## Success Metrics

### Phase 2 Success (AQA Complete)
- ✅ All 74 AQA subjects in specification_metadata
- ✅ >90% have components defined
- ✅ Subjects with options have constraints defined
- ✅ Total topics >30,000

### Phase 3 Success (International)
- ✅ Cambridge: 30+ subjects scraped
- ✅ IB: 20+ subjects (with documented limitations)
- ✅ Total international topics >20,000

### Phase 4 Success (Assessment Resources)
- ✅ Past 3 years of papers for top 30 subjects
- ✅ Mark scheme insights extracted with AI
- ✅ Examiner report insights extracted
- ✅ Question bank >1,000 questions

### Phase 5 Success (Pathway UI)
- ✅ Pathway selection works for History
- ✅ Constraints validated (no invalid selections)
- ✅ Fallback works for subjects without constraints
- ✅ Beta users successfully select pathways

---

## Quick Start Commands

```bash
# 1. Check what data already exists
python check_existing_data.py

# 2. Test batch processor (3 subjects only)
python batch_processor.py --test

# 3. Run full AQA batch (all 74 subjects)
python batch_processor.py

# 4. Test Cambridge scraper
python -m scrapers.international.cambridge_scraper --subject "Mathematics" --qual "IGCSE"

# 5. List all Cambridge subjects
python -m scrapers.international.cambridge_scraper --list
```

---

## Troubleshooting

### Batch Processor Fails

**Check:**
1. Environment variables set? (.env file)
2. Supabase connection working?
3. Check log file: `data/logs/batch_YYYYMMDD_HHMMSS.log`

**Resume from failure:**
```bash
# The processor saves state automatically
# Just run again - it will skip completed subjects
python batch_processor.py
```

### Scraper Can't Find PDF

**Check:**
1. Is the subject URL correct in config?
2. Has AQA changed their website structure?
3. Try manual download to test URL

**Manual override:**
```python
# In aqa_scraper_enhanced.py, add direct PDF URL:
SPEC_PDF_URLS = {
    ('History', 'A-Level'): 'https://direct-pdf-url.com/spec.pdf'
}
```

### AI Extraction Fails

**Check:**
1. ANTHROPIC_API_KEY set correctly?
2. API rate limits hit? (add delay)
3. PDF corrupted? (try re-download)

**Fallback:**
- Use simpler extraction (just metadata, skip detailed topics)
- Increase AI timeout in config
- Try different AI model (Claude vs Gemini)

---

## Next Steps

1. **TODAY:** Run `python check_existing_data.py`
2. **TODAY:** Review audit report, decide on strategy
3. **THIS WEEK:** Run batch processor for AQA (test mode first!)
4. **NEXT WEEK:** Cambridge & IB scrapers
5. **WEEKS 3-4:** Assessment resources scraper
6. **WEEKS 5-7:** Subject pathways UI in app

---

## Questions & Answers

**Q: What if I stop the batch processor mid-run?**
A: No problem! It saves state after each subject. Just run again and it resumes.

**Q: Can I run scrapers in parallel to speed up?**
A: Yes, but be careful with API rate limits. Better to run sequentially for reliability.

**Q: What if a subject fails to scrape?**
A: The batch processor continues with other subjects. Failed subjects are logged. You can re-run them individually later.

**Q: How often should we update the scraped data?**
A: Exam board specifications change annually (usually September). Run scrapers every 6-12 months.

**Q: What about other exam boards (OCR, Edexcel)?**
A: Same approach! Create similar batch processors. The infrastructure is reusable.

---

## Contact & Support

If you encounter issues:
1. Check the log files in `data/logs/`
2. Check the state files in `data/state/`
3. Review the audit report
4. Re-run in test mode to isolate issues

---

**Ready to start?** Run the audit tool first:
```bash
python check_existing_data.py
```

This will show you exactly where you stand and what to do next! 🚀
