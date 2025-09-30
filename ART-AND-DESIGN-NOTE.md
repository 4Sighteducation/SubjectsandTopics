# Art and Design - Special Handling

## The Situation

AQA has **6 different A-Level Art codes** but they're essentially ONE qualification:

- 7201: Art, craft and design
- 7202: Fine art
- 7203: Graphic communication
- 7204: Textile design
- 7205: Three-dimensional design
- 7206: Photography

**All share:**
- ✅ Same specification content (3.1-3.8)
- ✅ Same assessment structure
- ✅ Same components

**Only difference:**
- Student chooses their specialism (title) at enrollment

## The Solution

**In our database:**
- Store as **ONE subject**: "Art and Design A-Level" (code 7201)
- In `spec_components`: Add component saying "Choose 1 title from 6"
- Topics: The 8 content areas (3.1-3.8) common to all specialisms

**In your app:**
- User selects: "Art and Design A-Level"
- Then chooses: "Which specialism? (Fine art, Photography, etc.)"
- Then sees: The 8 content topics

## What The Scraper Does

The batch processor now **skips duplicate Art subjects** and only processes:
- One "Art and Design A-Level" (using code 7201)
- One "Art and Design GCSE" (using code 8201)

This simplifies everything and matches how the qualification actually works!


