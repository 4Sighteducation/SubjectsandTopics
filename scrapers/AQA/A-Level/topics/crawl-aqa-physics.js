/**
 * AQA PHYSICS A-LEVEL Scraper
 * Code: 7408
 * Numbered hierarchy + Tables with Content | Additional Information
 * Table Content rows = Level 3 topics
 * Contains physics notation (formulas like F=ma)
 */

import Firecrawl from '@mendable/firecrawl-js';
import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';

dotenv.config();

const fc = new Firecrawl({ apiKey: process.env.FIRECRAWL_API_KEY });
const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_KEY);

const SUBJECT = {
  name: 'Physics',
  code: '7408',
  qualification: 'A-Level',
  baseUrl: 'https://www.aqa.org.uk/subjects/physics/a-level/physics-7408/specification/subject-content'
};

async function crawlPhysics() {
  console.log('🔍 Crawling Physics...');
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

function parsePhysicsTopics(pages) {
  console.log('\n📋 Parsing Physics topics...');
  const allTopics = [];
  
  for (const page of pages) {
    const markdown = page.markdown || '';
    const pageTopics = parseNumberedWithTables(markdown);
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

function cleanMarkdown(text) {
  return text
    .replace(/\*\*(.+?)\*\*/g, '$1')
    .replace(/\*(.+?)\*/g, '$1')
    .replace(/_(.+?)_/g, '$1')
    .replace(/`(.+?)`/g, '$1')
    .trim();
}

function parseNumberedWithTables(markdown) {
  const topics = [];
  const lines = markdown.split('\n');
  let currentL0 = null;
  let currentL1 = null;
  let currentL2 = null;
  let inTable = false;
  let tableRowCounter = 1;
  
  for (const line of lines) {
    // Numbered headings (all levels)
    const numberedMatch = line.match(/^#{2,6}\s+(\d+(?:\.\d+)+)\s+(.+)$/);
    if (numberedMatch) {
      const code = numberedMatch[1];
      const title = cleanMarkdown(numberedMatch[2].trim());
      const level = code.split('.').length - 2;
      const parts = code.split('.');
      const parentCode = level > 0 ? parts.slice(0, -1).join('.') : null;
      
      topics.push({ code, title, level, parentCode });
      
      // Track current context
      if (level === 0) { currentL0 = code; currentL1 = null; currentL2 = null; }
      else if (level === 1) { currentL1 = code; currentL2 = null; }
      else if (level === 2) { currentL2 = code; }
      
      inTable = false;
      tableRowCounter = 1;
      continue;
    }
    
    // Detect table header
    if (line.includes('|') && (line.toLowerCase().includes('content') || line.toLowerCase().includes('additional'))) {
      inTable = true;
      tableRowCounter = 1;
      continue;
    }
    
    // Skip table separator
    if (line.match(/^\|[\s\-:]+\|/)) continue;
    
    // Parse table rows - Content column as Level 3 topics
    if (inTable && line.startsWith('|')) {
      const columns = line.split('|').map(c => c.trim()).filter(c => c);
      
      if (columns.length >= 1 && columns[0]) {
        const contentCell = cleanMarkdown(columns[0]);
        
        // Skip empty rows or header-like content
        if (!contentCell || contentCell.length < 5) continue;
        if (contentCell.toLowerCase().includes('content')) continue;
        
        // Create code under most specific current section
        const parent = currentL2 || currentL1 || currentL0;
        const code = `${parent}.${tableRowCounter}`;
        
        topics.push({
          code,
          title: contentCell,
          level: 3,
          parentCode: parent
        });
        
        tableRowCounter++;
      }
    }
    
    // Stop table on new heading
    if (inTable && line.match(/^#{2,6}/)) inTable = false;
  }
  
  return topics;
}

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
  console.log('🚀 PHYSICS');
  console.log('='.repeat(60));
  try {
    const pages = await crawlPhysics();
    const topics = parsePhysicsTopics(pages);
    await uploadToStaging(topics);
    console.log('\n✅ PHYSICS COMPLETE! Topics:', topics.length);
  } catch (error) {
    console.error('\n❌ FAILED:', error.message);
    process.exit(1);
  }
}

main();

