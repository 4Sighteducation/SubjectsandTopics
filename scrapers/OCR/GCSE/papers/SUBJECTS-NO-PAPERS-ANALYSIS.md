# Analysis: 12 Subjects with No Papers

## Subjects with Empty finder-results (from grep search):

1. **J203** - Sociology (listed as "Psychology" in dropdown)
2. **J625** - Religious Studies
3. **J730** - French  
4. **J731** - German
5. **J732** - Spanish
6. **J814** - Dance

## Likely Issues:

### Issue 1: Qualification Filter Names Don't Match
The batch script uses simplified names, but the dropdown requires exact matches including "(9-1)" and full qualification names.

**Example:**
- Batch script: `"Biology A - J247 (from 2016)"`
- Dropdown has: `"Gateway Science Suite - Biology A (9-1) - J247 (from 2016)"`

### Issue 2: Level Dropdown Not Selected
Some subjects (like Religious Studies J625) have the Level dropdown enabled but it's not being selected. The scraper needs to select "GCSE" (not "GCSE (Short course)").

### Issue 3: Wrong Subject Codes
- Ancient History: Batch uses `J051` but should be `J198`
- Geography A: Batch uses `J382` but should be `J383`

## Solution:

1. **Updated batch script** with correct qualification filter names
2. **Updated scraper** to select Level dropdown when enabled
3. **Fixed subject codes** (J198 for Ancient History, J383 for Geography A)

## Next Steps:

Re-run the batch script with the corrected qualification names. The scraper will now:
- Match qualification filters more accurately
- Select Level dropdown when needed
- Use correct subject codes

