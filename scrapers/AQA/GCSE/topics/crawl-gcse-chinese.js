/**
 * AQA GCSE CHINESE (MANDARIN) Scraper
 * Code: 8673
 * Full depth: Themes + Grammar + Vocabulary
 */

import Firecrawl from '@mendable/firecrawl-js';
import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';

dotenv.config({ path: '../../../../.env' });

const fc = new Firecrawl({ apiKey: process.env.FIRECRAWL_API_KEY });
const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_KEY);

const SUBJECT = {
  name: 'Chinese (Mandarin)',
  code: '8673',
  qualification: 'GCSE',
  baseUrl: 'https://www.aqa.org.uk/subjects/chinese-mandarin/gcse/chinese-mandarin-8673/specification/subject-content'
};

async function crawl() {
  console.log('🔍 Crawling GCSE Chinese...');
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

function parseChinese(pages) {
  console.log('\n📋 Parsing Chinese...');
  const topics = [];
  
  for (const page of pages) {
    const markdown = page.markdown || '';
    const lines = markdown.split('\n');
    let currentCode = null;
    
    for (const line of lines) {
      // All numbered headings
      const numberedMatch = line.match(/^#{2,6}\s+(\d+(?:\.\d+)+)\s+(.+)$/);
      if (numberedMatch) {
        const code = numberedMatch[1];
        const title = cleanMarkdown(numberedMatch[2].trim());
        const level = code.split('.').length - 2;
        const parentCode = level > 0 ? code.split('.').slice(0, -1).join('.') : null;
        topics.push({ code, title, level, parentCode });
        currentCode = code;
        continue;
      }
      
      // Topic bullets
      const topicMatch = line.match(/^[•\*-]\s+Topic (\d+):\s+(.+)$/);
      if (topicMatch && currentCode && currentCode.startsWith('3.1')) {
        const code = `${currentCode}.${topicMatch[1]}`;
        topics.push({ code, title: cleanMarkdown(topicMatch[2].trim()), level: 2, parentCode: currentCode });
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
  console.log('🚀 GCSE CHINESE (MANDARIN)');
  console.log('='.repeat(60));
  try {
    const pages = await crawl();
    const topics = parseChinese(pages);
    await upload(topics);
    console.log('\n✅ CHINESE COMPLETE!');
  } catch (error) {
    console.error('\n❌ FAILED:', error.message);
    process.exit(1);
  }
}

main();

