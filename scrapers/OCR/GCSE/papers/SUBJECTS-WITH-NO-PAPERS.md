# Subjects with No Papers Found

Based on analysis of debug HTML files, these subjects have empty `.finder-results` divs:

1. **J203** - Sociology (listed as "Psychology" in dropdown)
2. **J625** - Religious Studies  
3. **J730** - French
4. **J731** - German
5. **J732** - Spanish
6. **J814** - Dance

## Possible Reasons:

1. **Qualification filter name mismatch** - The filter name in batch script doesn't match dropdown exactly
2. **No papers available** - Subject might genuinely have no papers from 2019+
3. **Level selection needed** - Some subjects might need Level dropdown to be selected
4. **Wrong subject code** - Some codes might be incorrect

## Next Steps:

1. Check if qualification was selected correctly in debug HTML
2. Verify if Level dropdown needs to be selected
3. Check if these subjects genuinely have no papers available
4. Re-run with corrected qualification filter names

