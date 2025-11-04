/**
 * AQA GCSE HISTORY Scraper (FIXED)
 * Code: 8145
 * 4 levels: Sections → Period Studies (bold+dates) → Parts (bold "Part") → ignore bullets
 * Exclude: 3.1
 */

import Firecrawl from '@mendable/firecrawl-js';
import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';

dotenv.config({ path: '../../../../.env' });

const fc = new Firecrawl({ apiKey: process.env.FIRECRAWL_API_KEY });
const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_KEY);

const SUBJECT = {
  name: 'History',
  code: '8145',
  qualification: 'GCSE',
  baseUrl: 'https://www.aqa.org.uk/subjects/history/gcse/history-8145/specification/subject-content'
};

async function crawl() {
  console.log('🔍 Crawling GCSE History...');
  try {
    const mapResult = await fc.mapUrl(SUBJECT.baseUrl, { includeSubdomains: false, limit: 50 });
    const urls = mapResult.links || [];
    const contentUrls = urls.filter(u => 
      u.includes('/specification/subject-content/') && 
      !u.includes('/downloads/') && 
      u !== SUBJECT.baseUrl &&
      !u.includes('understanding-the-historic-environment') // Skip 3.1
    );
    
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
    console.error('❌ Failed:', error.message);
    throw error;
  }
}

function parseHistory(pages) {
  console.log('\n📋 Parsing GCSE History...');
  const allTopics = [];
  
  for (const page of pages) {
    const markdown = page.markdown || '';
    const pageTopics = parseHistoryStructure(markdown);
    allTopics.push(...pageTopics);
  }
  
  const unique = [];
  const seen = new Set();
  for (const topic of allTopics) {
    if (!seen.has(topic.code) && topic.code) { 
      unique.push(topic); 
      seen.add(topic.code); 
    }
  }
  
  console.log(`✅ Total: ${unique.length}`);
  const levels = {};
  unique.forEach(t => levels[t.level] = (levels[t.level] || 0) + 1);
  Object.keys(levels).sort().forEach(l => console.log(`   Level ${l}: ${levels[l]}`));
  
  return unique;
}

function parseHistoryStructure(markdown) {
  const topics = [];
  const lines = markdown.split('\n');
  let currentL0 = null;
  let currentL1 = null;
  let currentL2 = null;
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    
    // Level 0: Main sections (3.2, 3.3)
    const l0Match = line.match(/^#{2}\s+(\d+\.\d+)\s+(.+)$/);
    if (l0Match) {
      const code = l0Match[1];
      const title = l0Match[2].trim();
      topics.push({ code, title, level: 0, parentCode: null });
      currentL0 = code;
      currentL1 = null;
      currentL2 = null;
      continue;
    }
    
    // Level 1: Section markers (3.2.1 Section A: Period studies)
    const l1Match = line.match(/^#{3}\s+(\d+\.\d+\.\d+)\s+(.+)$/);
    if (l1Match) {
      const code = l1Match[1];
      const title = l1Match[2].trim();
      topics.push({ code, title, level: 1, parentCode: currentL0 });
      currentL1 = code;
      currentL2 = null;
      continue;
    }
    
    // Level 2: Period studies (4 hashes - #### AA America, 1840-1895)
    const l2Match = line.match(/^#{4}\s+([A-Z]{1,3})\s+(.+?),?\s+(\d{4}[-–]\d{4})(.*)$/);
    if (l2Match && currentL1) {
      const prefix = l2Match[1];
      const title = `${prefix} ${l2Match[2].trim()}, ${l2Match[3]}${l2Match[4]}`;
      const num = topics.filter(t => t.parentCode === currentL1).length + 1;
      const code = `${currentL1}.${num}`;
      topics.push({ code, title, level: 2, parentCode: currentL1 });
      currentL2 = code;
      continue;
    }
    
    // Level 3: Part headings (5 hashes - ##### Part one:...)
    const l3Match = line.match(/^#{5}\s+Part\s+(one|two|three|1|2|3):\s+(.+)$/i);
    if (l3Match && currentL2) {
      const title = `Part ${l3Match[1]}: ${l3Match[2].trim()}`;
      const num = topics.filter(t => t.parentCode === currentL2).length + 1;
      const code = `${currentL2}.${num}`;
      topics.push({ code, title, level: 3, parentCode: currentL2 });
    }
  }
  
  return topics;
}

async function upload(topics) {
  const { data: subject } = await supabase.from('staging_aqa_subjects').upsert({
    subject_name: `${SUBJECT.name} (${SUBJECT.qualification})`,
    subject_code: SUBJECT.code,
    qualification_type: SUBJECT.qualification,
    specification_url: 'https://www.aqa.org.uk/subjects/science/gcse/science-8464/specification'
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
}

async function main() {
  console.log('🚀 GCSE HISTORY');
  console.log('='.repeat(60));
  try {
    const pages = await crawl();
    const topics = parseHistory(pages);
    await upload(topics);
    console.log('\n✅ TRILOGY COMPLETE!');
  } catch (error) {
    console.error('\n❌ FAILED:', error.message);
    process.exit(1);
  }
}

main();

