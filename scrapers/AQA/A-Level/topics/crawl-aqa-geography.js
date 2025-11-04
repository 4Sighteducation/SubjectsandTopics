/**
 * AQA GEOGRAPHY A-LEVEL Scraper
 * Code: 7037
 * 
 * 4 URLs: 3.1, 3.2, 3.3, 3.4
 * Skip deep scrape of 3.3 (Fieldwork) - just Level 0-1
 * Deep scrape 3.1, 3.2, 3.4 to Level 4
 */

import Firecrawl from '@mendable/firecrawl-js';
import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';

dotenv.config();

const fc = new Firecrawl({ apiKey: process.env.FIRECRAWL_API_KEY });
const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_KEY);

const SUBJECT = {
  name: 'Geography',
  code: '7037',
  qualification: 'A-Level',
  baseUrl: 'https://www.aqa.org.uk/subjects/geography/a-level/geography-7037/specification/subject-content'
};

// Standard crawl
async function crawlGeography() {
  console.log('🔍 Crawling Geography...');
  try {
    const mapResult = await fc.mapUrl(SUBJECT.baseUrl, { includeSubdomains: false, limit: 50 });
    const urls = mapResult.links || [];
    const contentUrls = urls.filter(u => u.includes('/specification/subject-content/') && !u.includes('/downloads/') && u !== SUBJECT.baseUrl);
    
    console.log(`✅ Found ${contentUrls.length} pages`);
    const pages = [];
    for (let i = 0; i < contentUrls.length; i++) {
      const url = contentUrls[i];
      console.log(`   [${i + 1}] ${url.split('/').pop()}...`);
      try {
        const result = await fc.scrapeUrl(url, { formats: ['markdown'], onlyMainContent: true });
        pages.push({ ...result, url });
      } catch (err) { console.warn(`   ⚠️  Failed`); }
    }
    console.log(`✅ Scraped ${pages.length} pages`);
    return pages;
  } catch (error) {
    console.error('❌ Crawl failed:', error.message);
    throw error;
  }
}

// Parse with 3.3 limit
function parseGeographyTopics(pages) {
  console.log('\n📋 Parsing Geography topics...');
  const allTopics = [];
  
  for (const page of pages) {
    const markdown = page.markdown || '';
    const url = page.url || '';
    
    // Check if this is 3.3 (fieldwork)
    const is3_3 = url.includes('3-3') || url.includes('fieldwork');
    
    const pageTopics = parseGeographyPage(markdown, is3_3);
    allTopics.push(...pageTopics);
    
    if (is3_3) {
      console.log(`   3.3 Fieldwork: ${pageTopics.length} topics (limited to L0-1)`);
    }
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

function parseGeographyPage(markdown, limitTo2Levels = false) {
  const topics = [];
  const lines = markdown.split('\n');
  let currentCode = null;
  
  for (const line of lines) {
    // Numbered headings
    const numberedMatch = line.match(/^#{2,6}\s+(\d+(?:\.\d+)+)\s+(.+)$/);
    if (numberedMatch) {
      const code = numberedMatch[1];
      const title = numberedMatch[2].trim();
      const level = code.split('.').length - 2;
      
      // If limiting (3.3 fieldwork) and level > 1, skip
      if (limitTo2Levels && level > 1) continue;
      
      topics.push({ code, title, level, parentCode: level > 0 ? code.split('.').slice(0, -1).join('.') : null });
      
      // Track for bullets (only if not limiting or level <= 1)
      if (!limitTo2Levels || level <= 1) {
        currentCode = code;
      }
      continue;
    }
    
    // Bullets (skip if limiting and already deep enough)
    if (limitTo2Levels && currentCode && currentCode.split('.').length > 2) continue;
    
    const bulletMatch = line.match(/^-\s+[•·]?\s*(.{5,})/);
    if (bulletMatch && currentCode) {
      const bulletNum = topics.filter(t => t.parentCode === currentCode).length + 1;
      const bulletCode = `${currentCode}.${bulletNum}`;
      const level = currentCode.split('.').length - 1;
      
      topics.push({ code: bulletCode, title: bulletMatch[1].trim(), level, parentCode: currentCode });
    }
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
  console.log('🚀 GEOGRAPHY');
  console.log('='.repeat(60));
  try {
    const pages = await crawlGeography();
    const topics = parseGeographyTopics(pages);
    await uploadToStaging(topics);
    console.log('\n✅ GEOGRAPHY COMPLETE! Topics:', topics.length);
  } catch (error) {
    console.error('\n❌ FAILED:', error.message);
    process.exit(1);
  }
}

main();

