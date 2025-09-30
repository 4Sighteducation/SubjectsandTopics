# Curriculum Data Structure - Terminology & Plan

## What We Discovered in Supabase

### Successfully Uploaded ✅
- ✅ **Specification Metadata:** 1 record (AQA History A-Level overview)
- ✅ **Components:** 3 components (but some duplication - need to fix)
- ✅ **Selection Constraints:** 4 rules (geographic diversity, prohibited combos, chronological)
- ✅ **Topic Options:** 30 new records (1A Crusades, 1B Spain, 1C Tudors, etc.)
- ✅ **Total Topics for History:** 203 (30 new + 173 existing)

### The Data Looks Good!

Sample topic we uploaded:
```
1B: Spain in the Age of Discovery, 1469-1598
  Period: 1469-1598
  Region: European
  Level: 0
```

**This is perfect!** The choosable era is now in the database with rich metadata.

---

## The Hierarchy Problem - Different Names for Different Levels

### Current Confusion

The word "topic" means different things at different levels:

**In History:**
- Level 0 = "Option" or "Unit" (1B Spain - CHOOSABLE)
- Level 1 = "Study Area" (Part one: New Monarchy - REQUIRED if you chose 1B)
- Level 2 = "Content Point" (Charles' inheritance - specific flashcard material)

**In Mathematics:**
- Level 0 = "Module" (Pure Mathematics - ALL REQUIRED, no choice)
- Level 1 = "Topic" (Algebra and functions - ALL REQUIRED)
- Level 2 = "Subtopic" (Quadratic functions - ALL REQUIRED)

**In Your Current Database:**
All called "curriculum_topics" with `topic_level` 0, 1, 2

---

## Proposed Solution: Keep Current Schema, Clarify Meaning

### Don't Change Database Column Names! ✅

**Why:** Your app already works with `curriculum_topics` table. Changing it would break the app.

**Instead:** Use `topic_level` and metadata to distinguish:

| topic_level | Meaning | Is Selectable? | Has Rules? |
|-------------|---------|----------------|------------|
| 0 | Option/Unit/Module | Sometimes (check spec_components) | Check selection_constraints |
| 1 | Study Area/Topic | No (required if parent selected) | No |
| 2 | Content Point/Subtopic | No (all required) | No |

### How to Know if Level 0 is Choosable?

**Check the spec_components table:**
```sql
-- For History Component 1:
selection_type = 'choose_one'  → Level 0 topics ARE choosable
count_required = 1
total_available = 11

-- For Mathematics:
selection_type = 'required_all'  → Level 0 topics are ALL required
```

---

## What We Should Extract for Each Subject

### Minimum (What We Have Now):
✅ **Level 0 Options** - The choosable units
✅ **Component Structure** - How they're organized
✅ **Selection Rules** - If applicable

### Medium (Recommended Next):
❌ **Level 1 Study Areas** - The main topics within each option
- For History: "Part one: New Monarchy 1469-1556"
- For Math: "Algebra and functions"

### Maximum (Future):
❌ **Level 2 Content Points** - Specific flashcard material
- For History: "Charles' inheritance and consolidation"
- For Math: "Quadratic functions and graphs"

---

## Recommended Approach: Phased Extraction

### Phase 1: Current (What We've Done) ✅

**Extract:**
- Specification metadata
- Component structure
- Selection constraints
- **Level 0 only** (the options/modules)

**For History:** 30 choosable options (1A, 1B, etc.)  
**For Math:** ~12 main modules

**Status:** WORKING! ✅

**Pro:** Fast, cheap (~$0.10 per subject), enough for app beta  
**Con:** Not deeply detailed

---

### Phase 2: Medium Depth (Recommended for Production)

**Add extraction of Level 1 study areas**

For each Level 0 option, extract its main study areas.

**Example for History 1B (Spain):**
```
1B: Spain in the Age of Discovery [Level 0 - already have]
  ├─ Part one: the establishment of a 'New Monarchy', 1469-1556 [Level 1 - extract this]
  │   ├─ The forging of a new state, 1469-1516
  │   └─ The drive to 'Great Power' status, 1516-1556
  └─ Part two: Philip II's Spain, 1556-1598 [Level 1 - extract this]
      ├─ The 'Golden Age', 1556-1598
      └─ Spain: The 'Great Power', 1556-1598
```

**Example for Math:**
```
Pure Mathematics [Level 0]
  ├─ Algebra and functions [Level 1 - extract this]
  ├─ Coordinate geometry [Level 1 - extract this]
  └─ Calculus [Level 1 - extract this]
```

**Status:** NOT YET IMPLEMENTED

**Cost:** ~$0.30 per subject (3x more AI calls)  
**Benefit:** AI generates much better flashcards

---

### Phase 3: Maximum Depth (Future/Optional)

**Extract Level 2 content points**

For Math, this would be every specific skill.  
For History, this would be every bullet point.

**Status:** May not be necessary - Level 1 might be enough!

---

## Impact on Your App

### Current App Behavior (Won't Break!)

Your app currently:
1. Shows `user_subjects` (e.g., "History")
2. Shows `curriculum_topics` where `topic_level = 1` or all topics
3. User selects topics to study
4. Creates flashcards for selected topics

### With New Data (Enhances App!)

With enhanced data, app COULD:

**Option A: Keep Current Behavior (Safe)**
- Just show level 0 and 1 topics like before
- New metadata/constraints sit in database unused (for now)
- No app changes needed
- **This won't break anything!**

**Option B: Enhanced Selection Flow (Future v1.1)**
- For subjects with rules (History): guide user through selection
- Show "Choose your Component 1 option" → 11 choices
- Show "Choose your Component 2 option" → 20 choices
- Validate against constraints
- More accurate to real curriculum

---

## Recommendation for Your 2-Week Beta Timeline

### This Week: Baseline Extraction (Level 0 Only)

**What:**
- Extract Level 0 options for all major subjects
- AQA: History, Math, Biology, Chemistry, Physics, English
- OCR: Same subjects
- Total: ~20-30 subjects

**Why:**
- Fast (already working!)
- Cheap (~$3-5 total)
- Enough data for beta testing
- Won't block app launch

**Timeline:** 2-3 days

### Post-Beta: Deep Extraction (Add Level 1)

**What:**
- Go back and extract Level 1 study areas
- Enhances flashcard generation quality
- Better topic organization in app

**Why:**
- User feedback will tell us which subjects need it most
- More expensive - want to validate first
- Can roll out gradually

**Timeline:** After beta feedback

---

## Concerns Addressed

### "Will changing terminology break the app?"

**NO!** Because we're NOT changing terminology.

**We're using:**
- ✅ Same `curriculum_topics` table
- ✅ Same `topic_name` column
- ✅ Same `topic_level` column (already exists!)
- ✅ Just ADDING new topics at level 0

**Your app will:**
- ✅ Continue to work exactly as before
- ✅ See new level 0 options as additional topics
- ✅ Not break - it's purely additive

### "How to handle consistency across subjects?"

**Answer: Use the metadata!**

For each subject in database:
1. Check `spec_components.selection_type`:
   - `choose_one` → User must select from options
   - `required_all` → All topics are compulsory
   - `choose_multiple` → User selects N from M

2. App adapts behavior based on this flag

**No hardcoding needed!** The data tells the app how to behave.

---

## Proposed Plan Moving Forward

### TODAY: Verify & Document

**Tasks:**
1. ✅ Verify History data in Supabase (just did!)
2. ⬜ Check for duplicates in components table
3. ⬜ Document what each level means
4. ⬜ Create data dictionary

### TOMORROW: Test with Simple Subject

**Tasks:**
1. ⬜ Find AQA Mathematics PDF URL
2. ⬜ Run pipeline for Mathematics
3. ⬜ Compare: Does Math have selection rules? (probably not)
4. ⬜ Verify simpler subjects work too

### THIS WEEK: Expand AQA Coverage

**Tasks:**
1. ⬜ Add PDF URLs for 10-15 major AQA subjects
2. ⬜ Run pipeline for all subjects
3. ⬜ Analyze extraction quality
4. ⬜ Refine prompts based on results

### NEXT WEEK: Add Level 1 Extraction (Optional)

**Tasks:**
1. ⬜ Enhance extractor to get study areas
2. ⬜ Test with History 1B (your example)
3. ⬜ Decide if worth the cost/complexity
4. ⬜ Roll out if beneficial

---

## Decision Point

**For your 2-week beta launch, you have 3 options:**

### Option A: Ship with Level 0 Only (RECOMMENDED for Beta)
- ✅ Already working
- ✅ Fast to complete
- ✅ Enough for beta testing
- ✅ Won't delay app launch
- ⚠️ Less detailed than possible

### Option B: Add Level 1 Before Beta
- ✅ More detailed data
- ✅ Better AI flashcard generation
- ⚠️ More complex
- ⚠️ Higher cost (~$10-20 for all subjects)
- ⚠️ Might delay beta by 3-4 days

### Option C: Hybrid Approach
- ✅ Level 0 for most subjects
- ✅ Level 1 for top 5 subjects (History, English, etc.)
- ✅ Balanced cost/benefit
- ⚠️ Inconsistent depth

---

## My Recommendation

**For 2-Week Beta Timeline:**

1. **This Week:** Get Level 0 working for 20-30 subjects (AQA + OCR)
2. **Deploy Beta:** Launch with Level 0 data
3. **Gather Feedback:** See which subjects users struggle with
4. **Post-Beta:** Add Level 1 for subjects that need it based on user feedback

**This approach:**
- ✅ Doesn't delay beta
- ✅ Validates product-market fit first
- ✅ Optimizes investment based on real usage
- ✅ Allows iterative improvement

---

**What do you think? Should we:**
- A) Continue with Level 0 extraction for more subjects?
- B) Add Level 1 extraction now before expanding?
- C) Something else?

Let me know and we'll execute! 🚀
