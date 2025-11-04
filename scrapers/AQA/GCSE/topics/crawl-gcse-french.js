/**
 * AQA GCSE FRENCH Scraper (COMPLETE FIX)
 * Code: 8652
 * Full depth: Themes/Topics + Grammar subsections + Vocabulary
 */

import Firecrawl from '@mendable/firecrawl-js';
import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';

dotenv.config({ path: '../../../../.env' });

const fc = new Firecrawl({ apiKey: process.env.FIRECRAWL_API_KEY });
const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_KEY);

const SUBJECT = {
  name: 'French',
  code: '8652',
  qualification: 'GCSE',
  baseUrl: 'https://www.aqa.org.uk/subjects/french/gcse/french-8652/specification/subject-content'
};

async function crawl() {
  console.log('🔍 Crawling GCSE French (full depth)...');
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
        pages.push({ ...result, url: contentUrls[i], slug: contentUrls[i].split('/').pop() });
      } catch (err) { console.warn(`   ⚠️  Failed`); }
    }
    console.log(`✅ Scraped ${pages.length} pages`);
    return pages;
  } catch (error) {
    console.error('❌ Failed:', error.message);
    throw error;
  }
}

function cleanMarkdown(text) {
  return text
    .replace(/\*\*(.+?)\*\*/g, '$1')
    .replace(/\*(.+?)\*/g, '$1')
    .replace(/_(.+?)_/g, '$1')
    .replace(/`(.+?)`/g, '$1')
    .trim();
}

function parseFull(pages) {
  console.log('\n📋 Parsing GCSE French (all levels)...');
  const topics = [];
  
  for (const page of pages) {
    const markdown = page.markdown || '';
    const lines = markdown.split('\n');
    let currentL0 = null;
    let currentL1 = null;
    let currentL2 = null;
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      
      // Level 0: Main sections (3.1, 3.2, 3.3)
      const l0Match = line.match(/^#{2}\s+(\d+\.\d+)\s+(.+)$/);
      if (l0Match) {
        const code = l0Match[1];
        const title = cleanMarkdown(l0Match[2].trim());
        topics.push({ code, title, level: 0, parentCode: null });
        currentL0 = code;
        currentL1 = null;
        currentL2 = null;
        continue;
      }
      
      // Level 1: Themes OR Foundation/Higher tier (3.1.1, 3.2.1, etc.)
      const l1Match = line.match(/^#{3}\s+(\d+\.\d+\.\d+)\s+(.+)$/);
      if (l1Match) {
        const code = l1Match[1];
        const title = cleanMarkdown(l1Match[2].trim());
        topics.push({ code, title, level: 1, parentCode: currentL0 });
        currentL1 = code;
        currentL2 = null;
        continue;
      }
      
      // Level 2: Subsections (3.2.1.1 Noun phrases, etc.)
      const l2Match = line.match(/^#{4}\s+(\d+\.\d+\.\d+\.\d+)\s+(.+)$/);
      if (l2Match) {
        const code = l2Match[1];
        const title = cleanMarkdown(l2Match[2].trim());
        topics.push({ code, title, level: 2, parentCode: currentL1 });
        currentL2 = code;
        continue;
      }
      
      // Level 3: Bold headings (grammar/vocab details)
      if (currentL2 && line.match(/^\*\*[^*]+\*\*$/)) {
        const title = cleanMarkdown(line);
        if (title.length > 3) {
          const num = topics.filter(t => t.parentCode === currentL2).length + 1;
          const code = `${currentL2}.${num}`;
          topics.push({ code, title, level: 3, parentCode: currentL2 });
        }
        continue;
      }
      
      // Level 2: Topic bullets under themes (Topic 1:, Topic 2:)
      const topicMatch = line.match(/^[•\*-]\s+Topic (\d+):\s+(.+)$/);
      if (topicMatch && currentL1 && currentL1.startsWith('3.1')) {
        const code = `${currentL1}.${topicMatch[1]}`;
        const title = cleanMarkdown(topicMatch[2].trim());
        topics.push({ code, title, level: 2, parentCode: currentL1 });
      }
    }
  }
  
  console.log(`✅ Total: ${topics.length}`);
  const levels = {};
  topics.forEach(t => levels[t.level] = (levels[t.level] || 0) + 1);
  Object.keys(levels).sort().forEach(l => console.log(`   Level ${l}: ${levels[l]}`));
  
  return topics;
}

async function upload(topics) {
  const { data: subject } = await supabase.from('staging_aqa_subjects').upsert({
    subject_name: `${SUBJECT.name} (${SUBJECT.qualification})`,
    subject_code: SUBJECT.code,
    qualification_type: SUBJECT.qualification,
    specification_url: SUBJECT.baseUrl
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
  console.log('🚀 GCSE FRENCH');
  console.log('='.repeat(60));
  try {
    const pages = await crawl();
    const topics = parseFull(pages);
    await upload(topics);
    console.log('\n✅ GCSE FRENCH COMPLETE!');
  } catch (error) {
    console.error('\n❌ FAILED:', error.message);
    process.exit(1);
  }
}

main();
