/**
 * AQA FURTHER MATHEMATICS A-LEVEL Scraper
 * Code: 7367
 * 
 * Special structure: OT (Overarching Themes) codes in tables
 * 3.1 → 3.1.1 OT1 → Table rows (OT1.1, OT1.2) with Content column
 */

import Firecrawl from '@mendable/firecrawl-js';
import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';

dotenv.config();

const fc = new Firecrawl({ apiKey: process.env.FIRECRAWL_API_KEY });
const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_KEY);

const SUBJECT = {
  name: 'Further Mathematics',
  code: '7367',
  qualification: 'A-Level',
  baseUrl: 'https://www.aqa.org.uk/subjects/mathematics/a-level/mathematics-7367/specification/subject-content'
};

// Standard crawl
async function crawlFurtherMaths() {
  console.log('🔍 Crawling Further Maths...');
  try {
    const mapResult = await fc.mapUrl(SUBJECT.baseUrl, { includeSubdomains: false, limit: 50 });
    const urls = mapResult.links || [];
    const contentUrls = urls.filter(u => u.includes('/specification/subject-content/') && !u.includes('/downloads/') && u !== SUBJECT.baseUrl);
    
    console.log(`✅ Found ${contentUrls.length} pages`);
    const pages = [];
    for (let i = 0; i < contentUrls.length; i++) {
      console.log(`   [${i + 1}] ${contentUrls[i].split('/').pop()}...`);
      try {
        const result = await fc.scrapeUrl(contentUrls[i], { formats: ['markdown'], onlyMainContent: true });
        pages.push({ ...result, url: contentUrls[i] });
      } catch (err) { console.warn(`   ⚠️  Failed`); }
    }
    console.log(`✅ Scraped ${pages.length} pages`);
    return pages;
  } catch (error) {
    console.error('❌ Crawl failed:', error.message);
    throw error;
  }
}

// Parse OT codes from tables
function parseFurtherMathsTopics(pages) {
  console.log('\n📋 Parsing Further Maths topics...');
  const allTopics = [];
  
  for (const page of pages) {
    const markdown = page.markdown || '';
    const pageTopics = parseOTCodes(markdown);
    allTopics.push(...pageTopics);
  }
  
  const unique = [];
  const seen = new Set();
  for (const topic of allTopics) {
    if (!seen.has(topic.code) && topic.code) { unique.push(topic); seen.add(topic.code); }
  }
  
  console.log(`✅ Total: ${unique.length}`);
  const levels = {};
  unique.forEach(t => levels[t.level] = (levels[t.level] || 0) + 1);
  Object.keys(levels).sort().forEach(l => console.log(`   Level ${l}: ${levels[l]}`));
  
  return unique;
}

function parseOTCodes(markdown) {
  const topics = [];
  const lines = markdown.split('\n');
  let currentSectionCode = null;
  let currentSubsectionCode = null;  // ADDED!
  let inTable = false;
  
  for (const line of lines) {
    // Level 0: 3.1 Overarching themes
    const mainMatch = line.match(/^#{2,3}\s+(\d+\.\d+)\s+(.+)$/);
    if (mainMatch) {
      const code = mainMatch[1];
      const title = mainMatch[2].trim();
      topics.push({ code, title, level: 0, parentCode: null });
      currentSectionCode = code;
      continue;
    }
    
    // Level 2: Subsections (3.3.5 ME: Centres of mass, etc.) - Force Level 2!
    const subMatch = line.match(/^#{3,4}\s+(\d+\.\d+\.\d+)\s+([A-Z]{2,3}\d*):?\s+(.+)$/i);
    if (subMatch) {
      const code = subMatch[1];
      const prefix = subMatch[2];  // MA, ME, OT, DA, etc.
      const title = `${prefix}: ${subMatch[3].trim()}`;
      currentSubsectionCode = code;  // Use full code (3.3.5) as parent
      topics.push({ code, title, level: 2, parentCode: currentSectionCode });  // Level 2!
      continue;
    }
    
    // Table start
    if (line.includes('Content') || (line.startsWith('|') && line.includes('OT'))) {
      inTable = true;
    }
    
    // Skip separator
    if (line.match(/^\|?\s*[-:]+\s*\|/)) continue;
    
    // Table rows: OT1.1 | Content text OR DA1 | Content text
    if (inTable && line.startsWith('|')) {
      const cells = line.split('|').map(c => c.trim()).filter(c => c);
      
      // Check if first cell has ANY code pattern (MA1, ME6, OT1.1, DA1, etc.)
      if (cells.length >= 2 && cells[0].match(/^[A-Z]{2,3}\d+(\.\d+)?$/i)) {
        const code = cells[0];
        const content = cells[1];
        
        // Level 3: Table codes (ME1, MA2, etc.) with content
        topics.push({
          code,
          title: `${code} - ${content}`,
          level: 3,  // Level 3!
          parentCode: currentSubsectionCode  // Parent is 3.3.5, etc.
        });
      }
    }
    
    if (inTable && line.match(/^#{2,4}/)) inTable = false;
  }
  
  return topics;
}

// Standard upload
async function uploadToStaging(topics) {
  console.log('\n💾 Uploading...');
  try {
    const { data: subject } = await supabase.from('staging_aqa_subjects').upsert({
      subject_name: `${SUBJECT.name} (${SUBJECT.qualification})`, subject_code: SUBJECT.code,
      qualification_type: SUBJECT.qualification, specification_url: SUBJECT.baseUrl
    }, { onConflict: 'subject_code,qualification_type' }).select().single();
    
    console.log(`✅ Subject: ${subject.subject_name}`);
    await supabase.from('staging_aqa_topics').delete().eq('subject_id', subject.id);
    
    const toInsert = topics.map(t => ({ subject_id: subject.id, topic_code: t.code, topic_name: t.title, topic_level: t.level }));
    const { data: inserted } = await supabase.from('staging_aqa_topics').insert(toInsert).select();
    console.log(`✅ Uploaded ${inserted.length} topics`);
    
    const codeToId = new Map(inserted.map(t => [t.topic_code, t.id]));
    let linked = 0;
    for (const topic of topics) {
      if (topic.parentCode) {
        const parentId = codeToId.get(topic.parentCode);
        const childId = codeToId.get(topic.code);
        if (parentId && childId) {
          await supabase.from('staging_aqa_topics').update({ parent_topic_id: parentId }).eq('id', childId);
          linked++;
        }
      }
    }
    console.log(`✅ Linked ${linked} relationships`);
  } catch (error) {
    console.error('❌ Upload failed:', error);
    throw error;
  }
}

async function main() {
  console.log('🚀 FURTHER MATHEMATICS');
  console.log('='.repeat(60));
  try {
    const pages = await crawlFurtherMaths();
    const topics = parseFurtherMathsTopics(pages);
    await uploadToStaging(topics);
    console.log('\n✅ FURTHER MATHS COMPLETE! Topics:', topics.length);
  } catch (error) {
    console.error('\n❌ FAILED:', error.message);
    process.exit(1);
  }
}

main();

