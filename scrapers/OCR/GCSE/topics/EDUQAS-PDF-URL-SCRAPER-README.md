# Eduqas PDF URL Scraper

This scraper extracts specification PDF URLs from the Eduqas qualifications website for all subjects listed in the `Eduqas Qualifications - All.md` file.

## Overview

The scraper:
1. Parses the qualifications markdown file to extract all subjects and their levels (GCSE/A-Level)
2. Navigates to the Eduqas qualifications page (`https://www.eduqas.co.uk/ed/qualifications/`)
3. For each qualification, finds the subject's qualification page
4. Extracts the specification PDF URL from the subject page
5. Outputs all results to a JSON file

## Usage

### Test Run (First 5 Qualifications)

To test the scraper on a few subjects first:

```bash
# Windows
TEST-EDUQAS-PDF-URLS.bat

# Or manually
python eduqas-pdf-url-scraper.py --qualifications-file "Eduqas Qualifications - All.md" --output "eduqas-pdf-urls-test.json" --limit 5 --no-headless
```

### Full Run (All Qualifications)

To scrape all qualifications:

```bash
# Windows
RUN-EDUQAS-PDF-URLS.bat

# Or manually
python eduqas-pdf-url-scraper.py --qualifications-file "Eduqas Qualifications - All.md" --output "eduqas-pdf-urls.json"
```

### Command Line Options

- `--qualifications-file`: Path to the qualifications markdown file (default: `Eduqas Qualifications - All.md`)
- `--output`: Output JSON file path (default: `eduqas-pdf-urls.json`)
- `--no-headless`: Run browser in visible mode (useful for debugging)
- `--limit N`: Limit to first N qualifications (useful for testing)

## Output Format

The scraper outputs a JSON file with the following structure:

```json
{
  "Art and Design - GCSE": {
    "subject": "Art and Design",
    "level": "GCSE",
    "subject_page_url": "https://www.eduqas.co.uk/ed/qualifications/art-and-design-gcse/",
    "pdf_url": "https://www.eduqas.co.uk/media/ozvlit0g/eduqas-gcse-art-and-design-spec-from-2016-27-01-2020.pdf"
  },
  "Art and Design - A-Level": {
    "subject": "Art and Design",
    "level": "A-Level",
    "subject_page_url": "https://www.eduqas.co.uk/ed/qualifications/art-and-design-asa-level/",
    "pdf_url": "https://www.eduqas.co.uk/media/a3ndenvr/eduqas-a-level-art-and-design-spec-from-2015-e-090119.pdf"
  }
}
```

## PDF URL Patterns

Based on the examples provided, PDF URLs follow these patterns:

- **GCSE**: `https://www.eduqas.co.uk/media/{hash}/eduqas-gcse-{subject}-spec-from-{year}-{date}.pdf`
- **A-Level**: `https://www.eduqas.co.uk/media/{hash}/eduqas-a-level-{subject}-spec-from-{year}-e-{date}.pdf`
- **A-Level (short)**: `https://www.eduqas.co.uk/media/{hash}/eduqas-a-{subject}-spec-from-{year}.pdf`
- **Geography variants**: `https://www.eduqas.co.uk/media/{hash}/gcse-geog-{variant}-spec.pdf`

Note: The hash in the URL is unique per PDF and cannot be guessed, so the scraper must navigate the website to find the actual URLs.

## How It Works

1. **Parse Qualifications File**: Reads the markdown file and extracts subject names and levels
2. **Find Subject Pages**: Navigates the qualifications listing page and finds links to each subject's qualification page
3. **Extract PDF URLs**: For each subject page:
   - Waits for JavaScript to load dynamic content
   - Scrolls to trigger lazy loading
   - Looks for tabs/sections containing "Specification" or "Key Documents"
   - Searches for PDF links with "specification" or "spec" in the text
   - Returns the first matching PDF URL

## Troubleshooting

### No PDF URLs Found

If the scraper can't find PDF URLs:
1. Check that the subject page URL is correct
2. Try running with `--no-headless` to see what's happening
3. The website structure may have changed - check manually

### Subject Page Not Found

If subject pages aren't found:
1. The subject name in the file might not match the website
2. Check the qualifications page manually to see the exact naming
3. The website may use different terminology (e.g., "Art and Design" vs "Art & Design")

### Timeout Errors

If you get timeout errors:
1. Increase wait times in the code
2. Check your internet connection
3. The website may be slow - try running during off-peak hours

## Requirements

- Python 3.7+
- Selenium
- BeautifulSoup4
- Chrome browser and ChromeDriver

Install dependencies:
```bash
pip install selenium beautifulsoup4 requests
```

## Notes

- The scraper includes delays between requests to be polite to the server
- Some qualifications may fail - check the failed list in the output
- The scraper saves results incrementally, so partial results are available even if it stops early



