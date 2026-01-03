import Firecrawl from '@mendable/firecrawl-js';
import dotenv from 'dotenv';
import fs from 'fs';

dotenv.config();
const fc = new Firecrawl({ apiKey: process.env.FIRECRAWL_API_KEY });

const url = 'https://www.aqa.org.uk/subjects/music/a-level/music-7272/specification/subject-content/appraising-music';
const result = await fc.scrapeUrl(url, { formats: ['markdown'], onlyMainContent: true });
fs.writeFileSync('debug-music-markdown.md', result.markdown);
console.log('First 2000 chars:');
console.log(result.markdown.substring(0, 2000));
