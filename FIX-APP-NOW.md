# 🔧 FIX THE APP - Step by Step

**Problem:** Topics not showing when you select subjects  
**Solution:** Diagnose current state → Clean migration → Test

---

## 📋 STEP 1: DIAGNOSE (5 minutes)

### Run Diagnostic Queries

1. Open Supabase Dashboard → SQL Editor
2. Open file: `database/diagnostics/check-current-production-state.sql`
3. Copy ALL the SQL
4. Paste into Supabase and Run

### What To Look For:

**Check #4: "Topic Counts per Subject"**
- Does Accounting have any topics? 
- If 0 topics → That's why it shows "No topics yet"

**Check #5: "Accounting Subject Detail"**
- Is Accounting marked `is_current = true`?
- Which exam board is it under?

**Check #9: "Accounting in Production vs Staging"**
- Production: How many topics?
- Staging: How many topics?
- If staging has more → Good, migration will fix it!

### Expected Results:

```
Production Issues:
❌ Accounting: 0 topics (or broken data)
❌ Many subjects: 0 topics
❌ Old AQA data mixed with new?

Staging Data (Ready):
✅ Edexcel A-Level: 33 subjects, ~5,000 topics
✅ Edexcel GCSE: 28 subjects, ~1,065 topics
✅ Clean hierarchy, no duplicates
```

---

## 🚀 STEP 2: CLEAN MIGRATION (5 minutes)

### What This Does:

```
BEFORE:
exam_board_subjects: Broken/old data ❌
curriculum_topics: Missing/broken ❌

AFTER:
exam_board_subjects: Clean Edexcel data ✅
curriculum_topics: Full hierarchy ✅
```

### Run The Migration:

1. **IMPORTANT:** Still in Supabase SQL Editor
2. Open file: `database/migrations/migrate-staging-CLEAN-REPLACE.sql`
3. Copy ALL the SQL (includes safety checks)
4. Paste into Supabase
5. **READ the warning** (it deletes old curriculum data)
6. Click Run

### What Gets Deleted:
- ❌ Old curriculum subjects
- ❌ Old curriculum topics
- ❌ Broken relationships

### What Gets Preserved:
- ✅ User accounts
- ✅ User flashcards
- ✅ Study history
- ✅ All user data

### Expected Output:

```
SUBJECTS BY BOARD:
Edexcel | A_LEVEL | 33
Edexcel | GCSE | 28

TOPICS BY BOARD:
Edexcel | A_LEVEL | 5000+ topics, depth 5
Edexcel | GCSE | 1065+ topics, depth 4

ORPHANED TOPICS: 0
TOP SUBJECTS:
- Business: 613 topics
- Economics A: 663 topics
- Economics B: 660 topics
```

---

## ✅ STEP 3: TEST THE APP (3 minutes)

### Test Flow:

1. **Refresh your browser** (clear cache if needed)
2. **Create new test account** (or use existing)
3. **Select:** GCSE
4. **Select Exam Board:** Edexcel
5. **You should see:** 28 GCSE subjects
6. **Click:** Accounting (or Business)
7. **You should see:** Topics load! 🎉

### If Still Broken:

**Check these in order:**

1. **App reading correct tables?**
   ```sql
   -- Verify app's query works
   SELECT * FROM exam_board_subjects 
   WHERE exam_board_id = (SELECT id FROM exam_boards WHERE code = 'Edexcel')
   LIMIT 5;
   ```

2. **Subjects linked to topics?**
   ```sql
   SELECT 
     s.subject_name,
     COUNT(t.id) as topics
   FROM exam_board_subjects s
   LEFT JOIN curriculum_topics t ON s.id = t.exam_board_subject_id
   WHERE s.subject_name ILIKE '%accounting%'
   GROUP BY s.subject_name;
   ```

3. **Check app logs:**
   - Open browser console (F12)
   - Look for errors when clicking subject
   - Check network tab for failed API calls

---

## 🔍 WHY IT WAS BROKEN

### The Problem:

Your app queries:
```typescript
supabase
  .from('exam_board_subjects')  // Expected: Edexcel subjects
  .select(...)
  // Result: Old AQA data OR empty
```

```typescript
supabase
  .from('curriculum_topics')  // Expected: Topics for selected subject
  .eq('exam_board_subject_id', subjectId)
  // Result: No matching topics OR broken links
```

### The Fix:

Migration populates these tables with clean Edexcel data:
- ✅ 61 subjects properly linked to exam boards
- ✅ 10,000+ topics properly linked to subjects
- ✅ Full hierarchy preserved (parent_topic_id)
- ✅ All relationships intact

---

## 📊 VERIFICATION CHECKLIST

After migration, verify:

- [ ] Supabase shows success message
- [ ] Verification queries show expected counts
- [ ] No orphaned topics (count = 0)
- [ ] App loads exam type selection
- [ ] App shows Edexcel in exam board list
- [ ] Subjects list loads (33 A-Level or 28 GCSE)
- [ ] Clicking subject loads topics
- [ ] Topics show hierarchy (levels 0-4)
- [ ] Can create flashcards from topics

---

## 🆘 TROUBLESHOOTING

### "Migration failed with FK violation"
- Re-run migration (it's idempotent)
- Check qualification_types table exists

### "Subjects show but no topics"
- Check subject_id matching in query
- Verify `exam_board_subject_id` in curriculum_topics

### "Can't see Edexcel in app"
- Check `exam_boards.active = true`
- Verify app filters by `active = true`

### "Still see old AQA data"
- Migration didn't run fully
- Check transaction completed (COMMIT at end)

---

## 💾 BACKUP REMINDER

If you want to backup current data first:

```sql
-- Uncomment these lines in the migration SQL:
CREATE TABLE exam_board_subjects_backup_20251121 AS 
SELECT * FROM exam_board_subjects;

CREATE TABLE curriculum_topics_backup_20251121 AS 
SELECT * FROM curriculum_topics;
```

To restore (if needed):
```sql
DELETE FROM curriculum_topics;
DELETE FROM exam_board_subjects;

INSERT INTO exam_board_subjects SELECT * FROM exam_board_subjects_backup_20251121;
INSERT INTO curriculum_topics SELECT * FROM curriculum_topics_backup_20251121;
```

---

## 🎯 NEXT STEPS AFTER FIX

Once app works:

1. ✅ Test flashcard generation with full context
2. ✅ Verify all 61 subjects work
3. ✅ Check topic hierarchy displays correctly
4. 🚀 Plan next feature (AI search, grade sliders, exam papers)

---

**GO DIAGNOSE FIRST, THEN MIGRATE!** 🔧



