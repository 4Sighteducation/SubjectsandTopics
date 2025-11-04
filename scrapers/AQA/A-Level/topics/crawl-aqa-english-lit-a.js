/**
 * AQA ENGLISH LITERATURE A A-LEVEL Scraper
 * Code: 7712
 * 
 * UNIQUE: Catalog of set texts (books) in tables
 * Format: "Text, Author, Time period"
 */

import Firecrawl from '@mendable/firecrawl-js';
import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';

dotenv.config();

const fc = new Firecrawl({ apiKey: process.env.FIRECRAWL_API_KEY });
const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_KEY);

const SUBJECT = {
  name: 'English Literature A',
  code: '7712',
  qualification: 'A-Level',
  baseUrl: 'https://www.aqa.org.uk/subjects/english/a-level/english-7712/specification/subject-content'
};

// Crawl
async function crawlEnglishLitA() {
  console.log('🔍 Crawling English Lit A...');
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

// Parse set texts from tables
function parseEnglishLitATopics(pages) {
  console.log('\n📋 Parsing set texts (books)...');
  
  const allTopics = [];
  
  for (const page of pages) {
    const markdown = page.markdown || '';
    const pageTopics = parseSetTexts(markdown);
    allTopics.push(...pageTopics);
    if (pageTopics.length > 0) console.log(`   Found ${pageTopics.length} set texts`);
  }
  
  console.log(`\n✅ Total: ${allTopics.length} set texts`);
  
  return allTopics;
}

function parseSetTexts(markdown) {
  const topics = [];
  const lines = markdown.split('\n');
  
  let currentSectionCode = null;
  let currentOptionCode = null;
  let inTable = false;
  let bookCounter = 0;
  
  for (const line of lines) {
    // Main section headings (3.1, 3.2, 3.3)
    const sectionMatch = line.match(/^#{2,3}\s+(\d+\.\d+(?:\.\d+)?)\s+(.+)$/);
    if (sectionMatch) {
      currentSectionCode = sectionMatch[1];
      currentOptionCode = null;  // Reset option
      bookCounter = 0;
      
      // SKIP 3.3.3 (NEA prohibited texts - not for students)
      if (currentSectionCode === '3.3.3') {
        console.log('   ⏭️  Skipping 3.3.3 (prohibited texts)');
        currentSectionCode = null;  // Don't process books from this section
        continue;
      }
      
      topics.push({
        code: currentSectionCode,
        title: sectionMatch[2].trim(),
        level: 0,
        parentCode: null
      });
      continue;
    }
    
    // Option headings (Option 2A, Option 2B)
    const optionMatch = line.match(/^#{3,4}\s+(Option\s+\d+[A-Z])[:.\s]+(.+)$/i);
    if (optionMatch) {
      const optionCode = optionMatch[1].replace(/\s/g, '');  // "Option2A"
      currentOptionCode = currentSectionCode ? `${currentSectionCode}.${optionCode}` : optionCode;
      bookCounter = 0;
      
      topics.push({
        code: currentOptionCode,
        title: optionMatch[1] + ': ' + optionMatch[2].trim(),
        level: 1,
        parentCode: currentSectionCode
      });
      continue;
    }
    
    // Table headers
    if (line.includes('Author') && line.includes('Text') && line.includes('Time')) {
      inTable = true;
      continue;
    }
    
    if (line.match(/^\|?\s*[-:]+\s*\|/)) continue;
    
    // Book rows (Author | Text | Time period)
    if (inTable && line.startsWith('|')) {
      const cells = line.split('|').map(c => c.trim()).filter(c => c);
      
      if (cells.length >= 3 && cells[1].length > 3) {
        bookCounter++;
        const parentCode = currentOptionCode || currentSectionCode;
        const bookCode = parentCode ? `${parentCode}.${bookCounter}` : `B${bookCounter}`;
        
        // Format: "Text, Author, Time period"
        const title = `${cells[1]}, ${cells[0]}, ${cells[2]}`;
        
        topics.push({
          code: bookCode,
          title,
          level: currentOptionCode ? 2 : 1,  // Level 2 if under option, Level 1 if under section
          parentCode
        });
      }
    }
    
    if (inTable && line.match(/^#{2,4}/)) {
      inTable = false;
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
  console.log('🚀 ENGLISH LITERATURE A');
  console.log('='.repeat(60));
  try {
    const pages = await crawlEnglishLitA();
    const topics = parseEnglishLitATopics(pages);
    await uploadToStaging(topics);
    console.log('\n✅ COMPLETE! Set texts:', topics.length);
  } catch (error) {
    console.error('\n❌ FAILED:', error.message);
    process.exit(1);
  }
}

main();

