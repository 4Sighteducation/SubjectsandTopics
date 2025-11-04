/**
 * AQA ENGLISH LANGUAGE A-LEVEL Scraper
 * Code: 7701
 * Numbered headings (3.1, 3.1.1) + bullets (3 levels)
 */

import Firecrawl from '@mendable/firecrawl-js';
import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';

dotenv.config();

const fc = new Firecrawl({ apiKey: process.env.FIRECRAWL_API_KEY });
const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_KEY);

const SUBJECT = {
  name: 'English Language',
  code: '7702',  // FIXED: Was 7701
  qualification: 'A-Level',
  baseUrl: 'https://www.aqa.org.uk/subjects/english/a-level/english-7702/specification/subject-content'
};

// Standard crawl
async function crawlEnglishLang() {
  console.log('🔍 Crawling English Language...');
  try {
    const mapResult = await fc.mapUrl(SUBJECT.baseUrl, { includeSubdomains: false, limit: 50 });
    const urls = mapResult.links || [];
    console.log(`   Checking ${urls.length} total URLs...`);
    
    // DEBUG: Show all URLs
    if (urls.length < 10) {
      urls.forEach(u => console.log(`   - ${u}`));
    }
    
    const contentUrls = urls.filter(u => 
      u.includes('/english') &&
      !u.includes('/downloads/')
    );
    
    console.log(`✅ Found ${contentUrls.length} pages (relaxed filter)`);
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

// Parse numbered + bullets
function parseEnglishLangTopics(pages) {
  console.log('\n📋 Parsing English Language topics...');
  const allTopics = [];
  
  for (const page of pages) {
    const markdown = page.markdown || '';
    const pageTopics = parseNumberedWithBullets(markdown);
    allTopics.push(...pageTopics);
  }
  
  const unique = [];
  const seen = new Set();
  for (const topic of allTopics) {
    if (!seen.has(topic.code)) { unique.push(topic); seen.add(topic.code); }
  }
  
  console.log(`✅ Total: ${unique.length}`);
  const levels = {};
  unique.forEach(t => levels[t.level] = (levels[t.level] || 0) + 1);
  Object.keys(levels).sort().forEach(l => console.log(`   Level ${l}: ${levels[l]}`));
  
  return unique;
}

// Clean markdown formatting from text (italics, bold, etc.)
function cleanMarkdown(text) {
  return text
    .replace(/\*\*(.+?)\*\*/g, '$1')  // Remove bold **text**
    .replace(/\*(.+?)\*/g, '$1')      // Remove italics *text*
    .replace(/_(.+?)_/g, '$1')        // Remove italics _text_
    .replace(/`(.+?)`/g, '$1')        // Remove code `text`
    .trim();
}

function parseNumberedWithBullets(markdown) {
  const topics = [];
  const lines = markdown.split('\n');
  let currentCode = null;
  
  for (const line of lines) {
    // Numbered headings
    const numberedMatch = line.match(/^(#{2,6})\s+(\d+(?:\.\d+)+)\s+(.+)$/);
    if (numberedMatch) {
      const code = numberedMatch[2];
      const title = cleanMarkdown(numberedMatch[3].trim());
      const level = code.split('.').length - 2;
      topics.push({ code, title, level, parentCode: level > 0 ? code.split('.').slice(0, -1).join('.') : null });
      currentCode = code;
      continue;
    }
    
    // Bullets
    const bulletMatch = line.match(/^-\s+[•·]?\s*(.{5,})/);
    if (bulletMatch && currentCode) {
      const bulletNum = topics.filter(t => t.parentCode === currentCode).length + 1;
      const bulletCode = `${currentCode}.${bulletNum}`;
      topics.push({ code: bulletCode, title: cleanMarkdown(bulletMatch[1].trim()), level: currentCode.split('.').length - 1, parentCode: currentCode });
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
  console.log('🚀 ENGLISH LANGUAGE');
  console.log('='.repeat(60));
  try {
    const pages = await crawlEnglishLang();
    const topics = parseEnglishLangTopics(pages);
    await uploadToStaging(topics);
    console.log('\n✅ ENGLISH LANGUAGE COMPLETE! Topics:', topics.length);
  } catch (error) {
    console.error('\n❌ FAILED:', error.message);
    process.exit(1);
  }
}

main();

