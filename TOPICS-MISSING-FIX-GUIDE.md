# 🚨 Topics Missing - Diagnosis & Fix Guide

## Problem Summary

**Current State:**
- ✅ Exam boards exist (AQA, Edexcel, OCR, WJEC, CCEA, CIE, SQA, EDUQAS)
- ✅ Subjects exist (407 total across all boards)
- ❌ **ALL topics show 0 count** - topics are missing from production!

## Root Cause

1. **Subjects were migrated** from `staging_aqa_subjects` → `exam_board_subjects` ✅
2. **Topics were NOT migrated** from `staging_aqa_topics` → `curriculum_topics` ❌
3. The previous migration script had column name errors:
   - Used `full_name` instead of `name`
   - Used `ss.code` instead of `ss.subject_code`
   - Used `ss.name` instead of `ss.subject_name`
   - Only migrated Edexcel (not all boards)

## What I Fixed

### 1. Fixed Diagnostic Queries ✅

**File:** `database/diagnostics/check-current-production-state.sql`

**Changes:**
- Line 10: `full_name` → `name as full_name`
- Line 22: `full_name` → `name as full_name`
- Line 120: Added `s.` prefix to ambiguous columns
- Line 154: `s.code` → `s.subject_code`
- Line 161: `s.name` → `s.subject_name`

### 2. Fixed Edexcel-Only Migration Script ✅

**File:** `database/migrations/migrate-staging-to-production.sql`

**Changes:**
- Line 10: `full_name` → `name`
- Line 19: `full_name` → `name`
- Line 50-51: `ss.code` → `ss.subject_code`, `ss.name` → `ss.subject_name`
- Line 82: `ss.code` → `ss.subject_code`

### 3. Created Comprehensive Migration Script ✅

**File:** `database/migrations/migrate-all-staging-to-production.sql`

This NEW script migrates **ALL exam boards** at once:
- AQA
- Edexcel / EDEXCEL
- OCR
- WJEC
- EDUQAS
- CCEA
- CIE
- SQA

## How to Fix Production

### Option 1: Run Comprehensive Migration (RECOMMENDED)

**Use this if you want to migrate ALL exam boards from staging:**

```sql
-- Run this in Supabase SQL Editor:
-- File: database/migrations/migrate-all-staging-to-production.sql
```

**What it does:**
1. ✅ Ensures all exam boards exist
2. ✅ Ensures all qualification types exist
3. ✅ Migrates ALL subjects from staging
4. ✅ **Migrates ALL topics from staging** (the missing piece!)
5. ✅ Maintains parent-child topic relationships
6. ✅ Shows verification reports

**Expected Results:**
- Should migrate thousands of topics
- All subjects will show topic counts > 0
- Complete hierarchy with proper parent relationships

### Option 2: Run Edexcel-Only Migration

**Use this if you only want to fix Edexcel:**

```sql
-- Run this in Supabase SQL Editor:
-- File: database/migrations/migrate-staging-to-production.sql
```

### Option 3: Manual Verification First

**Check what's in staging before migrating:**

```sql
-- Count topics in staging by exam board
SELECT 
  s.exam_board,
  s.qualification_type,
  COUNT(DISTINCT s.id) as subjects,
  COUNT(t.id) as topics,
  MAX(t.topic_level) as max_depth
FROM staging_aqa_subjects s
LEFT JOIN staging_aqa_topics t ON s.id = t.subject_id
GROUP BY s.exam_board, s.qualification_type
ORDER BY s.exam_board, s.qualification_type;
```

**Expected output:** Should show thousands of topics per exam board

## Verification After Migration

Run the fixed diagnostic script:

```sql
-- File: database/diagnostics/check-current-production-state.sql
```

**Look for:**
- ✅ Topic counts > 0 for subjects
- ✅ No orphaned topics (count = 0)
- ✅ Max topic depth = 3 or 4 (hierarchical structure)
- ✅ Sample topics showing proper parent relationships

## Why This Happened

**Theory 1: Migration Never Ran for Topics**
- Subjects were migrated manually or via a different script
- Topic migration step was skipped or failed silently

**Theory 2: Previous Migration Had Errors**
- Column name mismatches caused INSERT to fail
- Transaction rolled back but subjects remained (if run without transaction)

**Theory 3: Staging Was Empty During Migration**
- Migration ran before topics were scraped
- Only subjects existed at migration time

## Next Steps

1. **✅ FIRST:** Run diagnostic to confirm staging has topics:
   ```sql
   SELECT COUNT(*) FROM staging_aqa_topics;
   ```

2. **IF staging has topics:** Run `migrate-all-staging-to-production.sql`

3. **IF staging is empty:** 
   - Check if topics are in a different table
   - Re-run scrapers to populate staging
   - Then migrate

4. **AFTER migration:** Run diagnostic again to verify topics loaded

## Safety Notes

⚠️ **The migration script:**
- Runs in a transaction (can ROLLBACK if needed)
- Deletes existing topics before inserting (clean slate)
- Keeps old subjects as archived (is_current = false)
- Preserves UUIDs for topic parent relationships

✅ **Safe to run multiple times** - uses ON CONFLICT to upsert

## Quick Commands

**Count topics in production:**
```sql
SELECT COUNT(*) FROM curriculum_topics;
```

**Count topics in staging:**
```sql
SELECT COUNT(*) FROM staging_aqa_topics;
```

**Count subjects in production:**
```sql
SELECT COUNT(*) FROM exam_board_subjects WHERE is_current = true;
```

## Files Changed

1. ✅ `database/diagnostics/check-current-production-state.sql` - Fixed
2. ✅ `database/migrations/migrate-staging-to-production.sql` - Fixed (Edexcel only)
3. ✅ `database/migrations/migrate-all-staging-to-production.sql` - NEW (All boards)
4. ✅ `TOPICS-MISSING-FIX-GUIDE.md` - This document

---

**TL;DR:** Topics weren't migrated. Run `migrate-all-staging-to-production.sql` to fix it.

