/**
 * AQA DANCE A-LEVEL Scraper
 * Code: 7237
 * 
 * HYBRID: Numbered hierarchy + bullets + tables
 * 3.1 → 3.1.1 → bullet points AND table content
 */

import Firecrawl from '@mendable/firecrawl-js';
import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';

dotenv.config();

const fc = new Firecrawl({ apiKey: process.env.FIRECRAWL_API_KEY });
const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_KEY);

const SUBJECT = {
  name: 'Dance',
  code: '7237',
  qualification: 'A-Level',
  baseUrl: 'https://www.aqa.org.uk/subjects/dance/a-level/dance-7237/specification/subject-content'
};

// Copy the Biology crawl function
async function crawlDance() {
  console.log('🔍 Crawling Dance...');
  
  try {
    const mapResult = await fc.mapUrl(SUBJECT.baseUrl, { includeSubdomains: false, limit: 50 });
    const urls = mapResult.links || [];
    const contentUrls = urls.filter(u => u.includes('/specification/subject-content/') && !u.includes('/downloads/') && !u.includes('sitemap'));
    
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

// Parse both bullets AND table content
function parseDanceTopics(pages) {
  console.log('\n📋 Parsing Dance topics...');
  
  const allTopics = [];
  
  for (const page of pages) {
    const markdown = page.markdown || '';
    const pageTopics = parseMixedFormat(markdown);
    allTopics.push(...pageTopics);
  }
  
  const unique = [];
  const seen = new Set();
  for (const topic of allTopics) {
    if (!seen.has(topic.code)) {
      unique.push(topic);
      seen.add(topic.code);
    }
  }
  
  console.log(`✅ Found ${unique.length} topics`);
  const levels = {};
  unique.forEach(t => levels[t.level] = (levels[t.level] || 0) + 1);
  Object.keys(levels).sort().forEach(l => console.log(`   Level ${l}: ${levels[l]}`));
  
  return unique;
}

function parseMixedFormat(markdown) {
  const topics = [];
  const lines = markdown.split('\n');
  
  let currentTopicCode = null;
  let bulletCounter = 0;
  let inTable = false;
  let rowCounter = 0;
  
  for (const line of lines) {
    // Numbered headings (3.1, 3.1.1, 3.1.2)
    const numberedMatch = line.match(/^(#{2,6})\s+(\d+(?:\.\d+)+)\s+(.+)$/);
    if (numberedMatch) {
      const code = numberedMatch[2];
      const title = numberedMatch[3].trim();
      const level = code.split('.').length - 2;
      
      topics.push({ code, title, level, parentCode: level > 0 ? code.split('.').slice(0, -1).join('.') : null });
      
      if (level === 1) {
        currentTopicCode = code;
        bulletCounter = 0;
        rowCounter = 0;
      }
      continue;
    }
    
    // Bullets
    const bulletMatch = line.match(/^-\s+[•·]?\s*(.{5,})/);
    if (bulletMatch && currentTopicCode && !inTable) {
      bulletCounter++;
      topics.push({
        code: `${currentTopicCode}.B${bulletCounter}`,
        title: bulletMatch[1].trim(),
        level: 2,
        parentCode: currentTopicCode
      });
    }
    
    // Tables
    if (line.includes('Knowledge') || line.includes('Physical')) {
      inTable = true;
    }
    
    if (inTable && line.startsWith('|')) {
      const cells = line.split('|').map(c => c.trim()).filter(c => c);
      if (cells.length >= 2 && cells[0].length > 5 && !cells[0].includes('---')) {
        rowCounter++;
        const rowCode = `${currentTopicCode}.T${rowCounter}`;
        topics.push({ code: rowCode, title: cells[0], level: 2, parentCode: currentTopicCode });
        
        // Parse bullets from second column
        if (cells[1]) {
          const bullets = cells[1].split(/[•·]/).filter(b => b.trim().length > 3);
          bullets.forEach((b, i) => {
            topics.push({ code: `${rowCode}.${i + 1}`, title: b.trim(), level: 3, parentCode: rowCode });
          });
        }
      }
    }
    
    if (inTable && line.match(/^#{2,6}/)) inTable = false;
  }
  
  return topics;
}

// Standard upload function
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
  console.log('🚀 DANCE');
  console.log('='.repeat(60));
  try {
    const pages = await crawlDance();
    const topics = parseDanceTopics(pages);
    await uploadToStaging(topics);
    console.log('\n✅ DANCE COMPLETE! Topics:', topics.length);
  } catch (error) {
    console.error('\n❌ FAILED:', error.message);
    process.exit(1);
  }
}

main();

