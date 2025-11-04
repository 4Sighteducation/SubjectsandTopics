/**
 * AQA ACCOUNTING A-LEVEL Scraper
 * Code: 7127
 * 
 * Accounting uses TABLE format:
 * - Content column: Main topics
 * - Additional information column: Details (bullets)
 * 
 * Different from Biology (numbered) and History (pathways)!
 */

import Firecrawl from '@mendable/firecrawl-js';
import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';
import fs from 'fs/promises';

dotenv.config();

const fc = new Firecrawl({ apiKey: process.env.FIRECRAWL_API_KEY });
const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_KEY);

const SUBJECT = {
  name: 'Accounting',
  code: '7127',
  qualification: 'A-Level',
  baseUrl: 'https://www.aqa.org.uk/subjects/accounting/a-level/accounting-7127/specification/subject-content'
};

// ================================================================
// STEP 1: CRAWL
// ================================================================

async function crawlAccounting() {
  console.log('🔍 Crawling AQA Accounting...');
  
  try {
    const mapResult = await fc.mapUrl(SUBJECT.baseUrl, {
      includeSubdomains: false,
      limit: 100
    });
    
    const urls = mapResult.links || [];
    const contentUrls = urls.filter(u => 
      u.includes('/specification/subject-content/') &&
      !u.includes('/downloads/')
    );
    
    console.log(`✅ Found ${contentUrls.length} content pages`);
    console.log('\n📚 Scraping pages...');
    
    const pages = [];
    for (let i = 0; i < contentUrls.length; i++) {
      const url = contentUrls[i];
      console.log(`   [${i + 1}/${contentUrls.length}] ${url.split('/').pop().substring(0, 40)}...`);
      
      try {
        const result = await fc.scrapeUrl(url, {
          formats: ['markdown', 'html'],  // Need HTML to parse tables properly
          onlyMainContent: true
        });
        pages.push({ ...result, url });
        
        // Save first page for debugging
        if (i === 0) {
          await fs.writeFile('debug-accounting-page.md', result.markdown || '');
          await fs.writeFile('debug-accounting-page.html', result.html || '');
        }
      } catch (err) {
        console.warn(`   ⚠️  Failed`);
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
// STEP 2: PARSE TABLES (Accounting-specific)
// ================================================================

async function parseAccountingTopics(pages) {
  console.log('\n📋 Parsing Accounting topics (table format)...');
  
  const allTopics = [];
  
  for (const page of pages) {
    const markdown = page.markdown || '';
    const html = page.html || '';
    const url = page.url || '';
    
    // Extract main topic code from URL or page
    const mainTopicMatch = url.match(/\/(\d+\.\d+)-/);
    const mainTopicCode = mainTopicMatch ? mainTopicMatch[1] : null;
    
    const pageTopics = parseAccountingPage(markdown, html, url, mainTopicCode);
    allTopics.push(...pageTopics);
    
    if (pageTopics.length > 0) {
      console.log(`   ${mainTopicCode || url.split('/').pop()}: ${pageTopics.length} topics`);
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
  
  const levels = {};
  unique.forEach(t => levels[t.level] = (levels[t.level] || 0) + 1);
  Object.keys(levels).sort().forEach(l => {
    console.log(`   Level ${l}: ${levels[l]} topics`);
  });
  
  return unique;
}

function parseAccountingPage(markdown, html, url, mainTopicCode) {
  const topics = [];
  const lines = markdown.split('\n');
  
  // First, try to extract main topic (Level 0)
  const mainTopicMatch = markdown.match(/^#{1,2}\s+(\d+\.\d+)\s+(.+)$/m);
  if (mainTopicMatch) {
    const code = mainTopicMatch[1];
    const title = mainTopicMatch[2];
    
    topics.push({
      code,
      title: title.trim(),
      level: 0,
      parentCode: null,
      url
    });
    
    mainTopicCode = code; // Update for children
  }
  
  // Parse table rows (Content | Additional information format)
  // In markdown, tables look like:
  // | Content | Additional information |
  // | --- | --- |
  // | General accounting concepts. | Concepts are: ... |
  
  let inTable = false;
  let rowCounter = 0;
  
  for (const line of lines) {
    // Detect table header
    if (line.includes('Content') && line.includes('Additional information')) {
      inTable = true;
      continue;
    }
    
    // Skip separator line
    if (line.match(/^\|?\s*[-:]+\s*\|/)) {
      continue;
    }
    
    // Parse table rows
    if (inTable && line.startsWith('|')) {
      const cells = line.split('|').map(c => c.trim()).filter(c => c);
      
      if (cells.length >= 2) {
        const content = cells[0];
        const additionalInfo = cells[1];
        
        // Skip if content is too short (probably header)
        if (content.length < 10) continue;
        
        rowCounter++;
        
        // Level 1: Content column
        const contentCode = mainTopicCode ? `${mainTopicCode}.${rowCounter}` : `T${rowCounter}`;
        topics.push({
          code: contentCode,
          title: content.replace(/\.$/, '').trim(),
          level: 1,
          parentCode: mainTopicCode,
          url
        });
        
        // Level 2: Parse bullets from Additional information
        if (additionalInfo && additionalInfo.length > 10) {
          // Remove HTML tags and split on bullets/breaks
          let cleanedInfo = additionalInfo
            .replace(/<br\s*\/?>/gi, '\n')  // Convert <br> to newlines
            .replace(/<[^>]+>/g, '');        // Remove other HTML tags
          
          // Split on bullet markers or newlines with dashes
          const bullets = cleanedInfo
            .split(/\n-\s*|\n•\s*|[•·]\s*/)
            .map(b => b.trim())
            .filter(b => b.length > 5 && !b.toLowerCase().startsWith('concepts are:') && !b.toLowerCase().startsWith('situations are:'));
          
          bullets.forEach((bullet, idx) => {
            const bulletCode = `${contentCode}.${idx + 1}`;
            topics.push({
              code: bulletCode,
              title: bullet.trim().replace(/\.$/, '').replace(/\n/g, ' '),
              level: 2,
              parentCode: contentCode,
              url
            });
          });
        }
      }
    }
    
    // Exit table when we hit next heading
    if (inTable && line.match(/^#{1,4}\s+/)) {
      inTable = false;
    }
  }
  
  return topics;
}

// ================================================================
// STEP 3: UPLOAD
// ================================================================

async function uploadToStaging(topics) {
  console.log('\n💾 Uploading to staging...');
  
  try {
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
    
    // DELETE old topics
    await supabase.from('staging_aqa_topics').delete().eq('subject_id', subject.id);
    console.log(`✅ Cleared old topics`);
    
    // Insert new
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
    
    // Link parents
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
  console.log('🚀 AQA ACCOUNTING SCRAPER');
  console.log('='.repeat(60));
  
  try {
    const pages = await crawlAccounting();
    const topics = await parseAccountingTopics(pages);
    const subjectId = await uploadToStaging(topics);
    await validate(subjectId);
    
    console.log('\n' + '='.repeat(60));
    console.log('✅ ACCOUNTING COMPLETE!');
    console.log('\nNext: Create scrape-accounting-papers.py');
    
  } catch (error) {
    console.error('\n❌ FAILED:', error.message);
    console.error(error.stack);
    process.exit(1);
  }
}

main();

