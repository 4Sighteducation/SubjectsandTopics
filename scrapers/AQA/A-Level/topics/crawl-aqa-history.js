/**
 * AQA HISTORY A-LEVEL Scraper
 * Code: 7042
 * 
 * History uses PATHWAY OPTIONS (1A-1W) with bullet point content
 * Different structure from Biology!
 */

import Firecrawl from '@mendable/firecrawl-js';
import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';
import fs from 'fs/promises';

dotenv.config();

const fc = new Firecrawl({ apiKey: process.env.FIRECRAWL_API_KEY });
const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_KEY);

const SUBJECT = {
  name: 'History',
  code: '7042',
  qualification: 'A-Level',
  baseUrl: 'https://www.aqa.org.uk/subjects/history/a-level/history-7042/specification/subject-content'
};

// ================================================================
// STEP 1: CRAWL
// ================================================================

async function crawlHistory() {
  console.log('🔍 Crawling AQA History...');
  
  try {
    const mapResult = await fc.mapUrl(SUBJECT.baseUrl, {
      includeSubdomains: false,
      limit: 200
    });
    
    const urls = mapResult.links || [];
    const contentUrls = urls.filter(u => 
      u.includes('/specification/subject-content/') &&
      !u.includes('/downloads/') &&
      !u.includes('sitemap')
    );
    
    console.log(`✅ Found ${contentUrls.length} pathway pages`);
    console.log('\n📚 Scraping each pathway...');
    
    const pages = [];
    for (let i = 0; i < contentUrls.length; i++) {
      const url = contentUrls[i];
      console.log(`   [${i + 1}/${contentUrls.length}] ${url.split('/').pop().substring(0, 40)}...`);
      
      try {
        const result = await fc.scrapeUrl(url, {
          formats: ['markdown'],
          onlyMainContent: true
        });
        pages.push({ ...result, url });
      } catch (err) {
        console.warn(`   ⚠️  Failed (continuing)`);
      }
    }
    
    console.log(`\n✅ Scraped ${pages.length} pages`);
    return pages;
  } catch (error) {
    console.error('❌ Crawl failed:', error.message);
    throw error;
  }
}

// ================================================================
// STEP 2: PARSE HISTORY STRUCTURE
// ================================================================

async function parseHistoryTopics(pages) {
  console.log('\n📋 Parsing History topics...');
  
  const allTopics = [];
  let firstPageSaved = false;
  
  for (const page of pages) {
    const markdown = page.markdown || '';
    const url = page.url || '';
    
    // Extract pathway code from URL (e.g., "1a-tudors" → "1A")
    const pathwayMatch = url.match(/\/(\d+[a-z])-/i);
    const pathwayCode = pathwayMatch ? pathwayMatch[1].toUpperCase() : null;
    
    if (!pathwayCode) {
      console.log(`   ⚠️  No pathway code found in ${url}`);
      continue;
    }
    
    const pageTopics = parseHistoryPage(markdown, pathwayCode, url);
    allTopics.push(...pageTopics);
    
    console.log(`   ${pathwayCode}: ${pageTopics.length} topics`);
    
    // Save first page for debugging
    if (!firstPageSaved && pageTopics.length > 0) {
      await fs.writeFile('debug-history-page.md', markdown);
      console.log(`   💾 Saved sample to debug-history-page.md`);
      firstPageSaved = true;
    }
  }
  
  // Remove duplicates
  const unique = [];
  const seen = new Set();
  
  for (const topic of allTopics) {
    const key = `${topic.code}:${topic.title}`;
    if (!seen.has(key)) {
      unique.push(topic);
      seen.add(key);
    }
  }
  
  console.log(`\n✅ Total unique topics: ${unique.length}`);
  
  // Show distribution
  const levels = {};
  unique.forEach(t => levels[t.level] = (levels[t.level] || 0) + 1);
  Object.keys(levels).sort().forEach(l => {
    console.log(`   Level ${l}: ${levels[l]} topics`);
  });
  
  return unique;
}

function parseHistoryPage(markdown, pathwayCode, url) {
  const topics = [];
  const lines = markdown.split('\n');
  
  // Counters for code generation
  let partCounter = 0;
  let sectionCounter = 0;
  let bulletCounter = 0;
  let totalBulletsFound = 0; // DEBUG
  
  let currentPartCode = null;
  let currentSectionCode = null;
  
  // Level 0: Pathway (1A, 1B, 2A, etc.)
  const pathwayTitle = extractPathwayTitle(markdown);
  if (pathwayTitle) {
    topics.push({
      code: pathwayCode,
      title: pathwayTitle,
      level: 0,
      parentCode: null,
      url
    });
  }
  
  // Parse line by line
  for (const line of lines) {
    // Level 1: Part headings (## Part one:, ## Part two:)
    const partMatch = line.match(/^#{2,3}\s+(Part\s+\w+:)\s*(.*)$/i);
    if (partMatch) {
      partCounter++;
      sectionCounter = 0; // Reset section counter for new part
      
      const partTitle = (partMatch[1] + ' ' + partMatch[2]).trim();
      currentPartCode = `${pathwayCode}.P${partCounter}`;
      
      topics.push({
        code: currentPartCode,
        title: partTitle,
        level: 1,
        parentCode: pathwayCode,
        url
      });
      continue;
    }
    
    // Level 2: Section headings (### The origins of conflict..., red headings)
    // These are H3 or H4 headings that are NOT "Part X:"
    const sectionMatch = line.match(/^#{3,4}\s+([^#\n]{10,})$/);
    if (sectionMatch && !sectionMatch[1].toLowerCase().startsWith('part')) {
      sectionCounter++;
      bulletCounter = 0; // Reset bullet counter
      
      const sectionTitle = sectionMatch[1].trim();
      currentSectionCode = currentPartCode ? 
        `${currentPartCode}.S${sectionCounter}` : 
        `${pathwayCode}.S${sectionCounter}`;
      
      topics.push({
        code: currentSectionCode,
        title: sectionTitle,
        level: 2,
        parentCode: currentPartCode || pathwayCode,
        url
      });
      continue;
    }
    
    // Level 3: Bullet points (- The condition of China in 1936...)
    const bulletMatch = line.match(/^-\s+(.{10,})/);
    if (bulletMatch) {
      totalBulletsFound++; // DEBUG
      
      if (currentSectionCode) {
        bulletCounter++;
        const bulletCode = `${currentSectionCode}.${bulletCounter}`;
        
        topics.push({
          code: bulletCode,
          title: bulletMatch[1].trim(),
          level: 3,
          parentCode: currentSectionCode,
          url
        });
      }
    }
  }
  
  // DEBUG logging
  if (totalBulletsFound > 0 && topics.filter(t => t.level === 3).length === 0) {
    console.log(`   ⚠️  DEBUG: Found ${totalBulletsFound} bullet lines but captured 0 Level 3 topics!`);
    console.log(`   currentSectionCode was: ${currentSectionCode}`);
  }
  
  return topics;
}

function extractPathwayTitle(markdown) {
  // Extract from first H1 or H2: "1A The Age of the Crusades, c1071-1204"
  const match = markdown.match(/^#{1,2}\s+(\d+[A-Z])\s+(.+)$/m);
  return match ? match[2].trim() : null;
}

// ================================================================
// STEP 3: UPLOAD
// ================================================================

async function uploadToStaging(topics) {
  console.log('\n💾 Uploading to staging...');
  
  try {
    // 1. Subject
    const { data: subject } = await supabase
      .from('staging_aqa_subjects')
      .upsert({
        subject_name: `${SUBJECT.name} (${SUBJECT.qualification})`,
        subject_code: SUBJECT.code,
        qualification_type: SUBJECT.qualification,
        specification_url: SUBJECT.baseUrl
      }, { onConflict: 'subject_code,qualification_type' })
      .select()
      .single();
    
    console.log(`✅ Subject: ${subject.subject_name}`);
    
    // 2. DELETE old topics (no duplicates!)
    await supabase.from('staging_aqa_topics').delete().eq('subject_id', subject.id);
    console.log(`✅ Cleared old topics`);
    
    // 3. Insert new topics
    const toInsert = topics.map(t => ({
      subject_id: subject.id,
      topic_code: t.code,
      topic_name: t.title,
      topic_level: t.level
    }));
    
    const { data: inserted } = await supabase
      .from('staging_aqa_topics')
      .insert(toInsert)
      .select();
    
    console.log(`✅ Uploaded ${inserted.length} topics`);
    
    // 4. Link parents
    const codeToId = new Map(inserted.map(t => [t.topic_code, t.id]));
    let linked = 0;
    
    for (const topic of topics) {
      if (topic.parentCode) {
        const parentId = codeToId.get(topic.parentCode);
        const childId = codeToId.get(topic.code);
        if (parentId && childId) {
          await supabase
            .from('staging_aqa_topics')
            .update({ parent_topic_id: parentId })
            .eq('id', childId);
          linked++;
        }
      }
    }
    
    console.log(`✅ Linked ${linked} relationships`);
    
    return subject.id;
  } catch (error) {
    console.error('❌ Upload failed:', error);
    throw error;
  }
}

// ================================================================
// STEP 4: VALIDATE
// ================================================================

async function validate(subjectId) {
  console.log('\n📊 Validation...');
  
  const { data: topics } = await supabase
    .from('staging_aqa_topics')
    .select('*')
    .eq('subject_id', subjectId)
    .order('topic_code');
  
  const levels = {};
  topics.forEach(t => levels[t.topic_level] = (levels[t.topic_level] || 0) + 1);
  
  console.log(`   Total: ${topics.length}`);
  Object.keys(levels).sort().forEach(l => {
    console.log(`   Level ${l}: ${levels[l]}`);
  });
  
  console.log('\n📋 Sample (first 20):');
  topics.slice(0, 20).forEach(t => {
    const indent = '  '.repeat(t.topic_level);
    console.log(`   ${indent}${t.topic_code} ${t.topic_name}`);
  });
}

// ================================================================
// MAIN
// ================================================================

async function main() {
  console.log('🚀 AQA HISTORY SCRAPER');
  console.log('='.repeat(60));
  
  try {
    const pages = await crawlHistory();
    const topics = await parseHistoryTopics(pages);
    const subjectId = await uploadToStaging(topics);
    await validate(subjectId);
    
    console.log('\n' + '='.repeat(60));
    console.log('✅ HISTORY COMPLETE!');
    console.log('\nNext: python scrape-history-papers.py');
    
  } catch (error) {
    console.error('\n❌ FAILED:', error.message);
    process.exit(1);
  }
}

main();

