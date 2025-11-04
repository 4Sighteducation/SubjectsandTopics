/**
 * AQA RELIGIOUS STUDIES A-LEVEL Scraper
 * Code: 7062
 * Standard numbered hierarchy (3.1 → 3.1.1 → bullets)
 * 2 main components: Philosophy/Ethics + Study of Religion (all options)
 */

import Firecrawl from '@mendable/firecrawl-js';
import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';

dotenv.config();

const fc = new Firecrawl({ apiKey: process.env.FIRECRAWL_API_KEY });
const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_KEY);

const SUBJECT = {
  name: 'Religious Studies',
  code: '7062',
  qualification: 'A-Level',
  baseUrl: 'https://www.aqa.org.uk/subjects/religious-studies/a-level/religious-studies-7062/specification/subject-content'
};

async function crawlRS() {
  console.log('🔍 Crawling Religious Studies...');
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

function parseRSTopics(pages) {
  console.log('\n📋 Parsing Religious Studies topics...');
  const allTopics = [];
  
  for (const page of pages) {
    const markdown = page.markdown || '';
    const pageTopics = parseNumberedWithBullets(markdown);
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

function parseNumberedWithBullets(markdown) {
  const topics = [];
  const lines = markdown.split('\n');
  let currentL0 = null;
  let currentL1 = null;
  let currentL2 = null;
  let skipIntroText = false;
  
  for (const line of lines) {
    // Level 0: Main sections (3.1, 3.2)
    const l0Match = line.match(/^#{2}\s+(\d+\.\d+)\s+(.+)$/);
    if (l0Match) {
      const code = l0Match[1];
      const title = cleanMarkdown(l0Match[2].trim());
      topics.push({ code, title, level: 0, parentCode: null });
      currentL0 = code;
      currentL1 = null;
      currentL2 = null;
      skipIntroText = false;
      continue;
    }
    
    // Level 1: Religion options (3.2.1 2A Buddhism, 3.2.2 2B Christianity, etc.)
    const l1Match = line.match(/^#{3}\s+(\d+\.\d+\.\d+)\s+(.+)$/);
    if (l1Match) {
      const code = l1Match[1];
      const title = cleanMarkdown(l1Match[2].trim());
      topics.push({ code, title, level: 1, parentCode: currentL0 });
      currentL1 = code;
      currentL2 = null;
      skipIntroText = true; // Skip intro bullets after this
      continue;
    }
    
    // Skip intro requirements section
    if (skipIntroText && (line.includes('They should develop') || line.includes('They should be able'))) {
      continue;
    }
    
    // Skip "Section A:", "Section B:" markers (4 hashes)
    const sectionMarkerMatch = line.match(/^#{4}\s+Section [AB]:/i);
    if (sectionMarkerMatch && currentL1) {
      skipIntroText = false; // Now we can start capturing content
      continue;
    }
    
    // Level 2: Actual topic headings (5 hashes - Sources of wisdom, Ultimate reality, etc.)
    const l2Match = line.match(/^#{5}\s+(.+)$/);
    if (l2Match && currentL1) {
      const title = cleanMarkdown(l2Match[1].trim());
      
      const sectionNum = topics.filter(t => t.parentCode === currentL1).length + 1;
      const code = `${currentL1}.${sectionNum}`;
      topics.push({ code, title, level: 2, parentCode: currentL1 });
      currentL2 = code;
      continue;
    }
    
    // Level 3: Content bullets (only capture AFTER we've seen actual topic headings)
    if (!skipIntroText && currentL2) {
      const bulletMatch = line.match(/^-\s+[•·]?\s*(.{10,})/);
      if (bulletMatch) {
        const bulletNum = topics.filter(t => t.parentCode === currentL2).length + 1;
        const bulletCode = `${currentL2}.${bulletNum}`;
        topics.push({ 
          code: bulletCode, 
          title: cleanMarkdown(bulletMatch[1].trim()), 
          level: 3, 
          parentCode: currentL2 
        });
      }
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
  console.log('🚀 RELIGIOUS STUDIES');
  console.log('='.repeat(60));
  try {
    const pages = await crawlRS();
    const topics = parseRSTopics(pages);
    await uploadToStaging(topics);
    console.log('\n✅ RELIGIOUS STUDIES COMPLETE! Topics:', topics.length);
  } catch (error) {
    console.error('\n❌ FAILED:', error.message);
    process.exit(1);
  }
}

main();

