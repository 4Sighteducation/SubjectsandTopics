# 🚀 RUN THIS MIGRATION NOW

**Time:** 5 minutes  
**Goal:** Move your staging data into production so FLASH app works again

---

## ✅ QUICK STEPS

### 1. Open Supabase Dashboard
Go to: https://supabase.com/dashboard/project/YOUR-PROJECT-ID

### 2. Open SQL Editor
- Click "SQL Editor" in left sidebar
- Click "New Query"

### 3. Copy & Paste SQL
Open this file:
```
flash-curriculum-pipeline/database/migrations/migrate-staging-to-production.sql
```

Copy ALL the SQL and paste into Supabase SQL Editor

### 4. Run It
- Click "Run" (or Ctrl+Enter)
- Wait ~10-30 seconds

### 5. Check Results
You should see at bottom:

```
Subjects Migrated: 61
Topics: ~10,000
No orphaned topics
```

---

## 📊 WHAT THIS DOES

```
BEFORE (Broken):
staging_aqa_subjects (61 Edexcel subjects) ❌ App doesn't read these
staging_aqa_topics (10,000 topics)        ❌ App doesn't read these

AFTER (Fixed):
exam_board_subjects (61 Edexcel subjects) ✅ App reads these!
curriculum_topics (10,000 topics)         ✅ App reads these!
```

---

## 🧪 TEST IN APP

After migration runs:

1. **Start FLASH app**
   ```bash
   cd FLASH
   npm start
   ```

2. **Navigate to:** Onboarding → Select Exam Type

3. **Select:** A-Level (or GCSE)

4. **Select Exam Board:** Edexcel

5. **You should see:** List of 33 A-Level subjects (or 28 GCSE)

6. **Select a subject:** e.g., Business

7. **You should see:** Topics load (613 topics for Business!)

---

## ❌ IF IT FAILS

### Error: "relation does not exist"
- Make sure you're in the right database
- Check you have `exam_boards` and `qualification_types` tables

### Error: "foreign key violation"
- Run the migration again (it's idempotent)
- Check logs for which FK is failing

### Error: "No subjects appear in app"
- Check `is_current = true` in exam_board_subjects
- Verify `exam_board_id` matches Edexcel's ID

### Still broken?
Run these verification queries in SQL Editor:

```sql
-- Check exam board exists
SELECT * FROM exam_boards WHERE code = 'Edexcel';

-- Check subjects exist
SELECT COUNT(*) FROM exam_board_subjects 
WHERE exam_board_id = (SELECT id FROM exam_boards WHERE code = 'Edexcel')
AND is_current = true;

-- Check topics exist
SELECT 
  s.subject_name,
  COUNT(t.id) as topics
FROM exam_board_subjects s
LEFT JOIN curriculum_topics t ON s.id = t.exam_board_subject_id
WHERE s.exam_board_id = (SELECT id FROM exam_boards WHERE code = 'Edexcel')
GROUP BY s.subject_name
ORDER BY topics DESC
LIMIT 10;
```

---

## 🎯 AFTER SUCCESS

Once app works:
1. ✅ Subjects load
2. ✅ Topics load with hierarchy
3. ✅ Flashcard generation works

Then you can:
- Test flashcard generation with full context
- Verify topic depth (should see 4-6 levels for Business/Economics)
- Plan next features (AI search, grade sliders, etc.)

---

## 📝 NOTES

- **Safe to re-run:** Migration is idempotent (can run multiple times)
- **No data loss:** Old data marked `is_current = false`, not deleted
- **Staging preserved:** `staging_aqa_*` tables untouched (keep for future updates)

---

**GO RUN IT NOW!** 🚀



