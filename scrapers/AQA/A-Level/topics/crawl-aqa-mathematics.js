/**
 * AQA MATHEMATICS A-LEVEL Scraper
 * Code: 7357
 * Special codes in tables: OT1.1, OT2.1, etc.
 * Similar structure to Further Maths
 */

import Firecrawl from '@mendable/firecrawl-js';
import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';

dotenv.config();

const fc = new Firecrawl({ apiKey: process.env.FIRECRAWL_API_KEY });
const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_KEY);

const SUBJECT = {
  name: 'Mathematics',
  code: '7357',
  qualification: 'A-Level',
  baseUrl: 'https://www.aqa.org.uk/subjects/mathematics/a-level/mathematics-7357/specification/subject-content'
};

async function crawlMathematics() {
  console.log('🔍 Crawling Mathematics...');
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

function parseMathematicsTopics(pages) {
  console.log('\n📋 Parsing Mathematics topics...');
  const allTopics = [];
  
  for (const page of pages) {
    const markdown = page.markdown || '';
    const pageTopics = parseSpecialCodes(markdown);
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

function parseSpecialCodes(markdown) {
  const topics = [];
  const lines = markdown.split('\n');
  let currentSectionCode = null;
  let currentSubsectionCode = null;
  let inTable = false;
  const codeCounters = {}; // Track sequential numbering per section
  
  for (const line of lines) {
    // Level 0: Main sections (3.1, 3.2, 3.3, etc.)
    const mainMatch = line.match(/^#{2,3}\s+(\d+\.\d+)\s+(.+)$/);
    if (mainMatch) {
      const code = mainMatch[1];
      const title = mainMatch[2].trim();
      topics.push({ code, title, level: 0, parentCode: null });
      currentSectionCode = code;
      currentSubsectionCode = null;
      codeCounters[code] = 1; // Reset counter for this section
      inTable = false;
      continue;
    }
    
    // Level 1: Subsections with letter codes (3.1.1 OT1:, etc.) - SKIP, handled in tables
    const subMatch = line.match(/^#{3,4}\s+(\d+\.\d+(?:\.\d+)?)\s+([A-Z]{1,3}\d*):?\s+(.+)$/i);
    if (subMatch) {
      currentSubsectionCode = subMatch[1];
      inTable = false;
      continue;
    }
    
    // Table start detection
    if (line.includes('Content') || (line.startsWith('|') && line.match(/[A-Z]{1,3}\d/))) {
      inTable = true;
    }
    
    // Skip table separator
    if (line.match(/^\|?\s*[-:]+\s*\|/)) continue;
    
    // Parse table rows with codes
    if (inTable && line.startsWith('|')) {
      const cells = line.split('|').map(c => c.trim()).filter(c => c);
      
      // Check for special codes: OT1.1, OT2.1, A1, B2, etc.
      if (cells.length >= 2 && cells[0].match(/^[A-Z]{1,3}\d+(\.\d+)?$/i)) {
        const originalCode = cells[0];
        const content = cells[1];
        
        // Get first content line as title
        const contentLines = content.split('\n').filter(l => l.trim());
        const firstLine = contentLines.length > 0 ? contentLines[0].trim().split(',')[0].trim() : originalCode;
        
        // Create sequential code under current section (e.g., 3.3.1, 3.3.2)
        const parentCode = currentSubsectionCode || currentSectionCode;
        const counter = codeCounters[parentCode] || 1;
        const newCode = `${parentCode}.${counter}`;
        codeCounters[parentCode] = counter + 1;
        
        // Add Level 1 topic with first content line as title
        topics.push({
          code: newCode,
          title: `${originalCode} - ${firstLine}`,
          level: 1,
          parentCode: parentCode
        });
      }
    }
    
    // Stop table parsing on new heading
    if (inTable && line.match(/^#{2,4}/)) inTable = false;
  }
  
  return topics;
}

async function uploadToStaging(topics) {
  console.log('\n💾 Uploading...');
  try {
    const { data: subject } = await supabase.from('staging_aqa_subjects').upsert({
      subject_name: `${SUBJECT.name} (${SUBJECT.qualification})`, 
      subject_code: SUBJECT.code,
      qualification_type: SUBJECT.qualification, 
      specification_url: SUBJECT.baseUrl
    }, { onConflict: 'subject_code,qualification_type' }).select().single();
    
    console.log(`✅ Subject: ${subject.subject_name}`);
    await supabase.from('staging_aqa_topics').delete().eq('subject_id', subject.id);
    
    const toInsert = topics.map(t => ({ 
      subject_id: subject.id, 
      topic_code: t.code, 
      topic_name: t.title, 
      topic_level: t.level 
    }));
    
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
  console.log('🚀 MATHEMATICS');
  console.log('='.repeat(60));
  try {
    const pages = await crawlMathematics();
    const topics = parseMathematicsTopics(pages);
    await uploadToStaging(topics);
    console.log('\n✅ MATHEMATICS COMPLETE! Topics:', topics.length);
  } catch (error) {
    console.error('\n❌ FAILED:', error.message);
    process.exit(1);
  }
}

main();

