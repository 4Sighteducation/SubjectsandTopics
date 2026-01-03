# Environment Setup Guide

## 📝 What You Need

**3 environment variables in `.env` file:**

1. **FIRECRAWL_API_KEY** - From firecrawl.dev (NOT Firebase!)
2. **SUPABASE_URL** - Your Supabase project URL
3. **SUPABASE_ANON_KEY** - Your Supabase anon/public key

---

## 🔧 Step-by-Step Setup

### 1. Get Firecrawl API Key

1. Go to https://firecrawl.dev
2. Sign up / Log in
3. Go to Dashboard
4. Copy your API key (starts with `fc-...`)

### 2. Get Supabase Credentials

You already have these from your FLASH app!

1. Go to your Supabase project dashboard
2. Settings → API
3. Copy:
   - **Project URL** (https://xxx.supabase.co)
   - **anon public** key (long JWT token)

### 3. Edit `.env` File

I created `.env` file in `flash-curriculum-pipeline` folder.

**Replace these values:**
```bash
FIRECRAWL_API_KEY=fc-your-actual-key-here
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=eyJhbGci...your-actual-key-here
```

---

## ✅ Verify Setup

Run this to check:
```bash
cd "C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline"
node -e "require('dotenv').config(); console.log('FIRECRAWL_API_KEY:', process.env.FIRECRAWL_API_KEY ? '✅ Set' : '❌ Missing'); console.log('SUPABASE_URL:', process.env.SUPABASE_URL ? '✅ Set' : '❌ Missing');"
```

If you see all ✅, you're ready!

---

## 📁 Where the `.env` File Goes

**ONLY ONE PLACE:**
```
flash-curriculum-pipeline/
├── .env  ← HERE! (I created this for you)
├── test-firecrawl-aqa-biology.js
├── scrapers/
└── ...
```

**NOT needed in:**
- ❌ FLASH/ folder (your main app doesn't need Firecrawl)
- ❌ Any other folders

---

## 🎯 Why Only Here?

- Firecrawl is ONLY used for scraping (in flash-curriculum-pipeline)
- Your FLASH app doesn't scrape - it just reads from Supabase
- So only the scraping scripts need the Firecrawl key

---

## Common Mistake You Made:

You wrote: `FIREBASE_API_KEY`  
Should be: `FIRECRAWL_API_KEY`

**Firebase** = Google's backend platform  
**Firecrawl** = Web scraping service we're using

Different services! 😊

---

## Ready to Test?

Once you've updated `.env` with your real keys, run:
```bash
cd flash-curriculum-pipeline
node test-firecrawl-aqa-biology.js
```

Need help getting the keys from Firecrawl or Supabase?

