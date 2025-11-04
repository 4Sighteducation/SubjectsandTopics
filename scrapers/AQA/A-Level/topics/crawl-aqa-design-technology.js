/**
 * AQA DESIGN AND TECHNOLOGY A-LEVEL Scraper
 * Code: 7552
 * 
 * Structure: Table format (like Accounting/Business)
 * Content | Potential links to maths and science columns
 */

import Firecrawl from '@mendable/firecrawl-js';
import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';

dotenv.config();

const fc = new Firecrawl({ apiKey: process.env.FIRECRAWL_API_KEY });
const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_KEY);

const SUBJECT = {
  name: 'Design and Technology',
  code: '7552',
  qualification: 'A-Level',
  baseUrl: 'https://www.aqa.org.uk/subjects/design-and-technology/a-level/design-and-technology-7552/specification/subject-content'
};

// Same as Accounting/Business - map sub-pages and parse tables
async function crawlDesignTech() {
  console.log('🔍 Crawling Design and Technology...');
  
  try {
    const mapResult = await fc.mapUrl(SUBJECT.baseUrl, { includeSubdomains: false, limit: 50 });
    const urls = mapResult.links || [];
    const contentUrls = urls.filter(u => u.includes('/specification/subject-content/') && !u.includes('/downloads/') && !u.includes('sitemap') && u !== SUBJECT.baseUrl);
    
    console.log(`✅ Found ${contentUrls.length} sub-pages`);
    
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

// Parse tables (same as Accounting)
function parseDesignTechTopics(pages) {
  console.log('\n📋 Parsing Design Tech topics...');
  
  const allTopics = [];
  
  for (const page of pages) {
    const markdown = page.markdown || '';
    const url = page.url || '';
    const mainCode = url.match(/\/(\d+\.\d+)-/)?.[1];
    const pageTopics = parseTablePage(markdown, mainCode);
    allTopics.push(...pageTopics);
    if (pageTopics.length > 0) console.log(`   ${mainCode || url.split('/').pop()}: ${pageTopics.length} topics`);
  }
  
  const unique = [];
  const seen = new Set();
  for (const topic of allTopics) {
    if (!seen.has(topic.code)) { unique.push(topic); seen.add(topic.code); }
  }
  
  console.log(`\n✅ Total: ${unique.length}`);
  const levels = {};
  unique.forEach(t => levels[t.level] = (levels[t.level] || 0) + 1);
  Object.keys(levels).sort().forEach(l => console.log(`   Level ${l}: ${levels[l]}`));
  
  return unique;
}

function parseTablePage(markdown, mainCode) {
  const topics = [];
  const lines = markdown.split('\n');
  
  // Main topic
  const mainMatch = markdown.match(/^#{1,2}\s+(\d+\.\d+)\s+(.+)$/m);
  if (mainMatch) {
    topics.push({ code: mainMatch[1], title: mainMatch[2].trim(), level: 0, parentCode: null });
    mainCode = mainMatch[1];
  }
  
  let inTable = false, rowCounter = 0;
  
  for (const line of lines) {
    if (line.includes('Content') && line.includes('Potential')) inTable = true;
    if (line.match(/^\|?\s*[-:]+\s*\|/)) continue;
    
    if (inTable && line.startsWith('|')) {
      const cells = line.split('|').map(c => c.trim()).filter(c => c);
      if (cells.length >= 1 && cells[0].length > 10) {
        rowCounter++;
        const code = mainCode ? `${mainCode}.${rowCounter}` : `T${rowCounter}`;
        topics.push({ code, title: cells[0].replace(/\.$/, '').trim(), level: 1, parentCode: mainCode });
        
        // Parse bullets from Content
        if (cells[0].includes('•') || cells[0].includes('<br>')) {
          let clean = cells[0].replace(/<br\s*\/?>/gi, '\n').replace(/<[^>]+>/g, '');
          const bullets = clean.split(/\n[•·-]\s*/).filter(b => b.length > 5);
          bullets.forEach((b, i) => topics.push({ code: `${code}.${i+1}`, title: b.trim(), level: 2, parentCode: code }));
        }
      }
    }
    
    if (inTable && line.match(/^#{1,4}/)) inTable = false;
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
  console.log('🚀 DESIGN AND TECHNOLOGY');
  console.log('='.repeat(60));
  try {
    const pages = await crawlDesignTech();
    const topics = parseDesignTechTopics(pages);
    await uploadToStaging(topics);
    console.log('\n✅ DESIGN AND TECHNOLOGY COMPLETE! Topics:', topics.length);
  } catch (error) {
    console.error('\n❌ FAILED:', error.message);
    process.exit(1);
  }
}

main();

