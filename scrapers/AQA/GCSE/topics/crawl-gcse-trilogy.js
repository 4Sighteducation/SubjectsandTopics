/**
 * AQA GCSE COMBINED SCIENCE TRILOGY Scraper (DEEP)
 * Code: 8464
 * Full 4-level structure from Biology, Chemistry, Physics pages
 */

import Firecrawl from '@mendable/firecrawl-js';
import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';

dotenv.config({ path: '../../../../.env' });

const fc = new Firecrawl({ apiKey: process.env.FIRECRAWL_API_KEY });
const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_KEY);

const SUBJECT = {
  name: 'Combined Science: Trilogy',
  code: '8464',
  qualification: 'GCSE'
};

const TRILOGY_URLS = [
  { science: 'Biology', code: '1', url: 'https://www.aqa.org.uk/subjects/science/gcse/science-8464/specification/biology-subject-content' },
  { science: 'Chemistry', code: '2', url: 'https://www.aqa.org.uk/subjects/science/gcse/science-8464/specification/chemistry-subject-content' },
  { science: 'Physics', code: '3', url: 'https://www.aqa.org.uk/subjects/science/gcse/science-8464/specification/physics-subject-content' }
];

async function crawlTrilogy() {
  console.log('🔍 Crawling Combined Science Trilogy (deep scrape)...');
  const allPages = [];
  
  for (const config of TRILOGY_URLS) {
    console.log(`\n📚 ${config.science}...`);
    try {
      const result = await fc.scrapeUrl(config.url, { formats: ['markdown'], onlyMainContent: true });
      allPages.push({ ...result, science: config.science, scienceCode: config.code });
    } catch (err) {
      console.warn(`   ⚠️  ${config.science} failed`);
    }
  }
  
  console.log(`\n✅ Scraped ${allPages.length}/3 sciences`);
  return allPages;
}

function cleanMarkdown(text) {
  return text
    .replace(/\*\*(.+?)\*\*/g, '$1')
    .replace(/\*(.+?)\*/g, '$1')
    .replace(/_(.+?)_/g, '$1')
    .replace(/`(.+?)`/g, '$1')
    .trim();
}

function parseTrilogy(pages) {
  console.log('\n📋 Parsing Trilogy (all 4 levels)...');
  const allTopics = [];
  
  for (const pageData of pages) {
    const science = pageData.science;
    const scienceCode = pageData.scienceCode;
    const markdown = pageData.markdown || '';
    const lines = markdown.split('\n');
    
    // Level 0: Science subject
    allTopics.push({ code: scienceCode, title: science, level: 0, parentCode: null });
    
    let currentL1 = null;
    let currentL2 = null;
    
    for (const line of lines) {
      // Level 1: Main topics (4.1 Cell biology, 4.2 Organisation, etc.)
      const l1Match = line.match(/^#{2,3}\s+(?:4\.)?(\d+)\s+(.+)$/);
      if (l1Match && !line.match(/^\d+\.\d+\.\d/)) {
        const num = l1Match[1];
        const title = cleanMarkdown(l1Match[2].trim());
        const code = `${scienceCode}.${num}`;
        allTopics.push({ code, title, level: 1, parentCode: scienceCode });
        currentL1 = code;
        currentL2 = null;
        continue;
      }
      
      // Level 2: Sub-sections (4.1.1 Cell structure, 4.1.2 Cell division, etc.)
      const l2Match = line.match(/^#{3,4}\s+(?:4\.)?(\d+\.\d+)\s+(.+)$/);
      if (l2Match && currentL1) {
        const fullNum = l2Match[1];
        const title = cleanMarkdown(l2Match[2].trim());
        const parts = fullNum.split('.');
        const code = `${scienceCode}.${parts[0]}.${parts[1]}`;
        const parentCode = `${scienceCode}.${parts[0]}`;
        allTopics.push({ code, title, level: 2, parentCode });
        currentL2 = code;
        continue;
      }
      
      // Level 3: Deep sub-sections (4.1.1.1, etc.)
      const l3Match = line.match(/^#{4,5}\s+(?:4\.)?(\d+\.\d+\.\d+)\s+(.+)$/);
      if (l3Match && currentL2) {
        const fullNum = l3Match[1];
        const title = cleanMarkdown(l3Match[2].trim());
        const parts = fullNum.split('.');
        const code = `${scienceCode}.${parts[0]}.${parts[1]}.${parts[2]}`;
        const parentCode = `${scienceCode}.${parts[0]}.${parts[1]}`;
        allTopics.push({ code, title, level: 3, parentCode });
      }
    }
  }
  
  // Deduplicate
  const unique = [];
  const seen = new Set();
  for (const topic of allTopics) {
    if (!seen.has(topic.code)) {
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
  const { data: inserted, error: insertError } = await supabase.from('staging_aqa_topics').insert(toInsert).select();
  
  if (insertError) {
    console.error('❌ Insert error:', insertError);
    throw insertError;
  }
  
  console.log(`✅ Uploaded ${inserted?.length || 0} topics`);
  
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
  console.log('🚀 GCSE COMBINED SCIENCE TRILOGY');
  console.log('='.repeat(60));
  try {
    const pages = await crawlTrilogy();
    const topics = parseTrilogy(pages);
    await upload(topics);
    console.log('\n✅ TRILOGY COMPLETE!');
  } catch (error) {
    console.error('\n❌ FAILED:', error.message);
    process.exit(1);
  }
}

main();
