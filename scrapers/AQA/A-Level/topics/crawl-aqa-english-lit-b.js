/**
 * AQA ENGLISH LITERATURE B A-LEVEL Scraper
 * Code: 7717
 * 
 * Similar to Lit A but different sections:
 * 3.1 Literary genres (tragedy, comedy) - set texts
 * 3.2 Texts and genres (crime, protest) - set texts
 * 3.3 Theory and independence - critical theories (NOT prohibited texts)
 */

import Firecrawl from '@mendable/firecrawl-js';
import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';

dotenv.config();

const fc = new Firecrawl({ apiKey: process.env.FIRECRAWL_API_KEY });
const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_KEY);

const SUBJECT = {
  name: 'English Literature B',
  code: '7717',
  qualification: 'A-Level',
  baseUrl: 'https://www.aqa.org.uk/subjects/english/a-level/english-7717/specification/subject-content'
};

// Standard crawl
async function crawlEnglishLitB() {
  console.log('🔍 Crawling English Lit B...');
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

// Parse set texts + critical theories (skip prohibited)
function parseEnglishLitBTopics(pages) {
  console.log('\n📋 Parsing set texts and theories...');
  
  const allTopics = [];
  
  for (const page of pages) {
    const markdown = page.markdown || '';
    const pageTopics = parseSetTextsAndTheories(markdown);
    allTopics.push(...pageTopics);
  }
  
  // Deduplicate by CODE ONLY (keep first occurrence)
  const unique = [];
  const seen = new Set();
  
  for (const topic of allTopics) {
    if (!seen.has(topic.code) && topic.code) {
      unique.push(topic);
      seen.add(topic.code);
    }
  }
  
  console.log(`✅ Total unique: ${unique.length} (removed ${allTopics.length - unique.length} duplicates)`);
  const levels = {};
  unique.forEach(t => levels[t.level] = (levels[t.level] || 0) + 1);
  Object.keys(levels).sort().forEach(l => console.log(`   Level ${l}: ${levels[l]}`));
  
  return unique;
}

function parseSetTextsAndTheories(markdown) {
  const topics = [];
  const lines = markdown.split('\n');
  
  let currentSectionCode = null;
  let inTable = false;
  let inProhibited = false;
  let bookCounter = 0;
  
  for (const line of lines) {
    // Section headings
    const sectionMatch = line.match(/^#{2,4}\s+(\d+\.\d+(?:\.\d+)?)\s+(.+)$/);
    if (sectionMatch) {
      currentSectionCode = sectionMatch[1];
      bookCounter = 0;
      
      // Check if this is the prohibited texts section
      if (sectionMatch[2].toLowerCase().includes('prohibited')) {
        console.log('   ⏭️  Skipping prohibited texts section');
        inProhibited = true;
        currentSectionCode = null;
        continue;
      } else {
        inProhibited = false;
      }
      
      topics.push({
        code: currentSectionCode,
        title: sectionMatch[2].trim(),
        level: 0,
        parentCode: null
      });
      continue;
    }
    
    // Skip if in prohibited section
    if (inProhibited) continue;
    
    // Critical theories (for 3.3 - as bullet points)
    // "narrative theory", "feminist theory", etc.
    const theoryMatch = line.match(/^-?\s*([a-z-]+\s+theory)$/i);
    if (theoryMatch && currentSectionCode && currentSectionCode.startsWith('3.3')) {
      bookCounter++;
      topics.push({
        code: `${currentSectionCode}.${bookCounter}`,
        title: theoryMatch[1].trim(),
        level: 1,
        parentCode: currentSectionCode
      });
      continue;
    }
    
    // Table headers
    if (line.includes('Author') && line.includes('Text')) {
      inTable = true;
      continue;
    }
    
    if (line.match(/^\|?\s*[-:]+\s*\|/)) continue;
    
    // Book rows (Author | Text | Time period)
    if (inTable && line.startsWith('|') && currentSectionCode) {
      const cells = line.split('|').map(c => c.trim()).filter(c => c);
      
      if (cells.length >= 2 && cells[1].length > 3) {
        bookCounter++;
        const bookCode = `${currentSectionCode}.${bookCounter}`;
        
        // Format: "Text, Author, Time period" (or just "Text, Author" if no time period)
        const title = cells.length >= 3 && cells[2] 
          ? `${cells[1]}, ${cells[0]}, ${cells[2]}`
          : `${cells[1]}, ${cells[0]}`;
        
        topics.push({
          code: bookCode,
          title,
          level: 1,
          parentCode: currentSectionCode
        });
      }
    }
    
    if (inTable && line.match(/^#{2,4}/)) inTable = false;
  }
  
  return topics;
}

// Standard upload
async function uploadToStaging(topics) {
  console.log('\n💾 Uploading...');
  try {
    const { data: subject, error: subjectError } = await supabase.from('staging_aqa_subjects').upsert({
      subject_name: `${SUBJECT.name} (${SUBJECT.qualification})`, subject_code: SUBJECT.code,
      qualification_type: SUBJECT.qualification, specification_url: SUBJECT.baseUrl
    }, { onConflict: 'subject_code,qualification_type' }).select().single();
    
    if (subjectError || !subject) {
      console.error('❌ Subject upsert failed:', subjectError);
      throw new Error('Subject upsert failed');
    }
    
    console.log(`✅ Subject: ${subject.subject_name}`);
    await supabase.from('staging_aqa_topics').delete().eq('subject_id', subject.id);
    
    const toInsert = topics.map(t => ({ subject_id: subject.id, topic_code: t.code, topic_name: t.title, topic_level: t.level }));
    const { data: inserted, error: insertError } = await supabase.from('staging_aqa_topics').insert(toInsert).select();
    
    if (insertError || !inserted) {
      console.error('❌ Topics insert failed:', insertError);
      throw new Error('Topics insert failed: ' + JSON.stringify(insertError));
    }
    
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
  console.log('🚀 ENGLISH LITERATURE B');
  console.log('='.repeat(60));
  try {
    const pages = await crawlEnglishLitB();
    const topics = parseEnglishLitBTopics(pages);
    await uploadToStaging(topics);
    console.log('\n✅ COMPLETE! Topics:', topics.length);
  } catch (error) {
    console.error('\n❌ FAILED:', error.message);
    process.exit(1);
  }
}

main();

