/**
 * AQA PHILOSOPHY A-LEVEL Scraper
 * Code: 7172
 * Standard numbered hierarchy + Set Texts sections
 * Special: Set Texts take next sequential number (e.g., 3.1.5 if stops at 3.1.4)
 */

import Firecrawl from '@mendable/firecrawl-js';
import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';

dotenv.config();

const fc = new Firecrawl({ apiKey: process.env.FIRECRAWL_API_KEY });
const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_KEY);

const SUBJECT = {
  name: 'Philosophy',
  code: '7172',
  qualification: 'A-Level',
  baseUrl: 'https://www.aqa.org.uk/subjects/philosophy/a-level/philosophy-7172/specification/subject-content'
};

async function crawlPhilosophy() {
  console.log('🔍 Crawling Philosophy...');
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

function parsePhilosophyTopics(pages) {
  console.log('\n📋 Parsing Philosophy topics...');
  const allTopics = [];
  
  for (const page of pages) {
    const markdown = page.markdown || '';
    const pageTopics = parseWithSetTexts(markdown);
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

function parseWithSetTexts(markdown) {
  const topics = [];
  const lines = markdown.split('\n');
  let currentL0 = null;
  let currentL0Title = '';
  let currentL1 = null;
  let maxL1Number = 0;
  
  for (const line of lines) {
    // Level 0: Main sections (3.1, 3.2, 3.3, 3.4)
    const l0Match = line.match(/^#{2}\s+(\d+\.\d+)\s+(.+)$/);
    if (l0Match) {
      const code = l0Match[1];
      const title = cleanMarkdown(l0Match[2].trim());
      topics.push({ code, title, level: 0, parentCode: null });
      currentL0 = code;
      currentL0Title = title;
      currentL1 = null;
      maxL1Number = 0;
      continue;
    }
    
    // Level 1: Numbered subsections (3.1.1, 3.1.2, etc.)
    const l1Match = line.match(/^#{3,4}\s+(\d+\.\d+\.\d+)\s+(.+)$/);
    if (l1Match) {
      const code = l1Match[1];
      const title = cleanMarkdown(l1Match[2].trim());
      const parts = code.split('.');
      const num = parseInt(parts[2]);
      if (num > maxL1Number) maxL1Number = num;
      
      topics.push({ code, title, level: 1, parentCode: currentL0 });
      currentL1 = code;
      continue;
    }
    
    // Special: "Set Texts" heading
    const setTextsMatch = line.match(/^#{3,4}\s+Set\s+[Tt]exts?$/i);
    if (setTextsMatch && currentL0) {
      const nextNum = maxL1Number + 1;
      const code = `${currentL0}.${nextNum}`;
      topics.push({ 
        code, 
        title: `${currentL0Title} Set Texts`, 
        level: 1, 
        parentCode: currentL0 
      });
      currentL1 = code;
      maxL1Number = nextNum;
      continue;
    }
    
    // Bullets (including set text references)
    const bulletMatch = line.match(/^-\s+[•·]?\s*(.{5,})/);
    if (bulletMatch && currentL1) {
      const bulletNum = topics.filter(t => t.parentCode === currentL1).length + 1;
      const bulletCode = `${currentL1}.${bulletNum}`;
      topics.push({ 
        code: bulletCode, 
        title: cleanMarkdown(bulletMatch[1].trim()), 
        level: 2, 
        parentCode: currentL1 
      });
    }
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
  console.log('🚀 PHILOSOPHY');
  console.log('='.repeat(60));
  try {
    const pages = await crawlPhilosophy();
    const topics = parsePhilosophyTopics(pages);
    await uploadToStaging(topics);
    console.log('\n✅ PHILOSOPHY COMPLETE! Topics:', topics.length);
  } catch (error) {
    console.error('\n❌ FAILED:', error.message);
    process.exit(1);
  }
}

main();

