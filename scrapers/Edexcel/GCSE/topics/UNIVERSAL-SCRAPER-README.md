# Universal Edexcel GCSE Subject Scraper

This system allows you to scrape **any** Edexcel GCSE subject by simply creating a small YAML configuration file. No code changes needed!

## 📁 Files

```
scrapers/Edexcel/GCSE/topics/
├── universal-stage1-upload.py     # Stage 1: Upload structure
├── universal-stage2-scrape.py     # Stage 2: Extract PDF content
├── run-subject.bat                # Easy runner script
├── SUBJECT-CONFIG-TEMPLATE.yaml   # Template for new subjects
└── configs/
    ├── geography-a.yaml           # Geography A config
    ├── geography-b.yaml           # Geography B config
    └── business.yaml              # (Add more subjects here...)
```

## 🚀 Usage

### Run an Existing Subject

```bash
# From the topics folder:
cd scrapers/Edexcel/GCSE/topics

# Geography A
run-subject.bat geography-a

# Geography B
run-subject.bat geography-b
```

This will:
1. **Stage 1**: Upload the subject structure (Components → Topics → Optional Subtopics)
2. **Stage 2**: Extract detailed content from the PDF specification

## 📝 Adding a New Subject

### Step 1: Create Config File

Copy the template:

```bash
copy SUBJECT-CONFIG-TEMPLATE.yaml configs/business.yaml
```

### Step 2: Fill in the Configuration

Open `configs/business.yaml` and fill in:

```yaml
subject:
  code: "GCSE-Business"          # From SUBJECT-CODES.py
  name: "Business"               # Subject name
  qualification: "GCSE"
  exam_board: "Edexcel"
  pdf_url: "https://..."         # Specification PDF URL

scraping:
  page_range: "7-30"             # Pages with content tables
  table_flavor: "lattice"        # Usually "lattice"

components:
  - code: "Component1"
    title: "Component 1: Title from spec"
  # Add all components...

topics:
  - code: "Component1_Topic1"
    title: "Topic 1: Title from spec"
    parent: "Component1"
  # Add all topics...

optional_subtopics:
  - code: "Component1_Topic1_1A"
    title: "1A: Optional topic title"
    parent: "Component1_Topic1"
    detect_in_text:              # Patterns to detect in PDF
      - "Optional sub topic 1A"
      - "Specific phrase from PDF"
  # Add if subject has optional subtopics...

topic_to_component:
  "1": "Component1"
  "2": "Component1"
  # Map topic numbers to components...
```

### Step 3: Run the Scraper

```bash
run-subject.bat business
```

That's it! The universal scraper will:
- ✅ Create the subject in Supabase
- ✅ Upload all components, topics, and optional subtopics
- ✅ Extract all key ideas from the PDF tables
- ✅ Extract all detailed content (a, b, c...)
- ✅ Build proper hierarchical relationships

## 📊 Config File Guide

### Required Fields

#### `subject`
- `code`: Standardized code from `SUBJECT-CODES.py` (e.g., `GCSE-Business`)
- `name`: Subject name (e.g., `Business`)
- `pdf_url`: URL to the Edexcel specification PDF

#### `scraping`
- `page_range`: Pages to scan for tables (e.g., `"7-30"`)
- `table_flavor`: Table extraction method (`"lattice"` or `"stream"`)

#### `components`
Array of components (usually 3 papers):
```yaml
- code: "Component1"              # Must be unique
  title: "Component 1: Full title with paper code"
```

#### `topics`
Array of topics under components:
```yaml
- code: "Component1_Topic1"       # Format: {ComponentCode}_Topic{N}
  title: "Topic 1: Title"
  parent: "Component1"            # Parent component code
```

### Optional Fields

#### `optional_subtopics`
For subjects with optional topic choices:
```yaml
- code: "Component1_Topic1_1A"
  title: "1A: Optional topic title (optional - choose X from Y)"
  parent: "Component1_Topic1"
  detect_in_text:
    - "Text patterns to identify this section in PDF"
```

#### `exit_optional_patterns`
Regex patterns that signal exit from optional subtopic section:
```yaml
exit_optional_patterns:
  - "Topic [5-9]:"
```

#### `topic_to_component`
Maps topic numbers to components (for correct parenting):
```yaml
topic_to_component:
  "1": "Component1"
  "2": "Component1"
  "3": "Component2"
```

## 🎯 How It Works

### Stage 1: Structure Upload
1. Reads the YAML config
2. Creates subject in `staging_aqa_subjects`
3. Creates all components (Level 0)
4. Creates all topics (Level 1)
5. Creates all optional subtopics (Level 2) if any
6. Links parent-child relationships

### Stage 2: PDF Content Extraction
1. Downloads the specification PDF
2. Extracts tables from specified pages using Camelot
3. Detects optional subtopic sections using text patterns
4. Extracts key ideas (e.g., "1.1 Title") as Level 2 or 3
5. Extracts detailed content (a, b, c...) as Level 3 or 4
6. Handles multi-line content and split headers
7. Creates proper parent-child relationships

## 🔍 Finding Config Information

### 1. Subject Code
Look in `SUBJECT-CODES.py` for the standardized code.

### 2. Components and Topics
Open the PDF specification, usually on pages 3-5:
- Look for "Content overview" sections
- Components are usually "Paper 1", "Paper 2", etc.
- Topics are numbered lists under each component

### 3. Page Range
Open the PDF and find:
- Where content tables start (usually page 7-10)
- Where they end (usually page 25-40)
- Use format: `"7-30"`

### 4. Optional Subtopics
Look in the spec for:
- "Optional sub topic"
- "Choose X from Y"
- "Optional questions"

Then find those exact phrases in the PDF for `detect_in_text` patterns.

## 📋 Examples

### Simple Subject (No Optional Subtopics)
Like **Business** - just components and topics, no options.

### Complex Subject (With Optional Subtopics)
Like **Geography A** - has optional subtopics 1A, 1B, 1C (choose 2 from 3) and 6A, 6B (choose 1 from 2).

## 🐛 Troubleshooting

### "Subject not found" error
- Make sure Stage 1 ran successfully first
- Check subject code matches exactly

### Missing topics in output
- Check `page_range` covers all content tables
- Try changing `table_flavor` from `lattice` to `stream`
- Check for section headers in tables (handled automatically)

### Optional subtopic not detected
- Add more patterns to `detect_in_text`
- Check exact phrases in the PDF
- Ensure patterns are unique to that subtopic

### Wrong parent assignments
- Update `topic_to_component` mapping
- Check component codes match exactly

## 🎉 Benefits of This System

- ✅ **No code duplication** - one scraper for all subjects
- ✅ **Easy to add subjects** - just create a ~50 line YAML file
- ✅ **Consistent structure** - all subjects follow same pattern
- ✅ **Future-proof** - works with any Edexcel GCSE spec format
- ✅ **Maintainable** - config changes don't require code changes
- ✅ **Context-efficient** - saves ~1000 lines per subject vs duplication

## 📚 Next Steps

1. Test with Geography A and B
2. Add Business, History, Music, etc. using the template
3. Share config files - others can reuse them
4. Consider creating configs for A-Level subjects too

---

**Questions?** Check the template file or existing configs for examples!


