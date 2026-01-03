# OCR GCSE Papers Scraping Issues Summary

## Issues Found

### 1. Wrong Subject Codes
- **Ancient History**: Batch script uses `J051` but should be `J198`
- **Geography A**: Batch script uses `J382` but should be `J383`

### 2. Wrong Qualification Filter Names
The qualification filter names in the batch script don't match the dropdown exactly. They need to include "(9-1)" and full qualification names.

### 3. Subjects That May Have No Papers
Some subjects might genuinely have no papers available from 2019 onwards, or the qualification filter wasn't selected correctly.

## Correct Qualification Filters (from HTML dropdown)

Based on the debug HTML files, here are the CORRECT qualification filter names:

- Ancient History: `"Ancient History (9-1) - J198 (from 2017)"` (code: J198)
- Art and Design: `"Art and Design (9-1) - J170-J176 (from 2016)"`
- Biology A: `"Gateway Science Suite - Biology A (9-1) - J247 (from 2016)"`
- Biology B: `"Twenty First Century Science Suite - Biology B (9-1) - J257 (from 2016)"`
- Business: `"Business (9-1) - J204 (from 2017)"`
- Chemistry A: `"Gateway Science Suite - Chemistry A (9-1) - J248 (from 2016)"`
- Chemistry B: `"Twenty First Century Science Suite - Chemistry B (9-1) - J258 (from 2016)"`
- Citizenship Studies: `"Citizenship Studies (9-1) - J270 (from 2016)"`
- Classical Civilisation: `"Classical Civilisation (9-1) - J199 (from 2017)"`
- Combined Science A: `"Gateway Science Suite - Combined Science A (9-1) - J250 (from 2016)"`
- Combined Science B: `"Twenty First Century Science Suite - Combined Science B (9-1) - J260 (from 2016)"`
- Computer Science: `"Computer Science (9-1) - J277 (from 2020)"`
- Dance: `"Dance (9-1) - J814 (from 2016)"`
- Design and Technology: `"Design and Technology (9-1) - J310 (from 2017)"`
- Drama: `"Drama (9-1) - J316 (from 2016)"`
- Economics: `"Economics (9-1) - J205 (from 2017)"`
- English Language: `"English Language (9-1) - J351"` (no "from" date)
- English Literature: `"English Literature (9-1) - J352 (from 2015)"`
- Food Preparation and Nutrition: `"Food Preparation and Nutrition (9-1) - J309 (from 2016)"`
- French: `"French (9-1) - J730 (from 2016)"`
- Geography A: `"Geography A (Geographical Themes) (9-1) - J383 (from 2016)"` (code: J383)
- Geography B: `"Geography B (Geography for Enquiring Minds) (9-1) - J384 (from 2016)"`
- German: `"German (9-1) - J731 (from 2016)"`
- History A: `"History A (Explaining the Modern World) (9-1) - J410 (from 2016)"`
- History B: `"History B (Schools History Project) (9-1) - J411 (from 2016)"`
- Latin: `"Latin (9-1) - J282 (from 2016)"`
- Mathematics: `"Mathematics (9-1) - J560 (from 2015)"`
- Media Studies: `"Media Studies (9-1) - J200 (from 2023)"`
- Music: `"Music (9-1) - J536 (from 2016)"`
- Physical Education: `"Physical Education (9-1) - J587 (from 2016)"`
- Physics A: `"Gateway Science Suite - Physics A (9-1) - J249 (from 2016)"`
- Physics B: `"Twenty First Century Science Suite - Physics B (9-1) - J259 (from 2016)"`
- Religious Studies: `"Religious Studies (9-1) - J625, J125 (from 2016)"`
- Sociology: `"Psychology (9-1) - J203 (from 2017)"` (Note: Listed as Psychology but code is J203)
- Spanish: `"Spanish (9-1) - J732 (from 2016)"`

## Subjects Not in Dropdown
- Classical Greek (J292) - appears in dropdown but not in our batch script
- Some subjects might not have papers available

## Next Steps
1. Check debug HTML files for subjects with empty `.finder-results` divs
2. Verify qualification was selected correctly
3. Re-run batch script with corrected qualification names





















