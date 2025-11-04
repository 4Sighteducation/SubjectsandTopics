/**
 * AQA BUSINESS A-LEVEL Scraper
 * Code: 7132
 * 
 * Structure: TABLE format (like Accounting)
 * Content | Additional information columns
 */

import Firecrawl from '@mendable/firecrawl-js';
import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';

dotenv.config();

const fc = new Firecrawl({ apiKey: process.env.FIRECRAWL_API_KEY });
const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_KEY);

const SUBJECT = {
  name: 'Business',
  code: '7132',
  qualification: 'A-Level',
  baseUrl: 'https://www.aqa.org.uk/subjects/business/a-level/business-7132/specification/subject-content'
};

// ================================================================
// STEP 1: CRAWL
// ================================================================

async function crawlBusiness() {
  console.log('🔍 Crawling Business...');
  
  try {
    const mapResult = await fc.mapUrl(SUBJECT.baseUrl, {
      includeSubdomains: false,
      limit: 100
    });
    
    const urls = mapResult.links || [];
    const contentUrls = urls.filter(u => 
      u.includes('/specification/subject-content/') &&
      !u.includes('/downloads/') &&
      !u.includes('sitemap')
    );
    
    console.log(`✅ Found ${contentUrls.length} content pages`);
    
    const pages = [];
    for (let i = 0; i < contentUrls.length; i++) {
      const url = contentUrls[i];
      console.log(`   [${i + 1}] ${url.split('/').pop().substring(0, 50)}...`);
      
      try {
        const result = await fc.scrapeUrl(url, {
          formats: ['markdown', 'html'],
          onlyMainContent: true
        });
        pages.push({ ...result, url });
      } catch (err) {
        console.warn(`   ⚠️  Failed`);
      }
    }
    
    console.log(`✅ Scraped ${pages.length} pages`);
    return pages;
  } catch (error) {
    console.error('❌ Crawl failed:', error.message);
    throw error;
  }
}

// ================================================================
// STEP 2: PARSE TABLES
// ================================================================

function parseBusinessTopics(pages) {
  console.log('\n📋 Parsing Business topics (table format)...');
  
  const allTopics = [];
  
  for (const page of pages) {
    const markdown = page.markdown || '';
    const url = page.url || '';
    
    const mainTopicMatch = url.match(/\/(\d+\.\d+)-/);
    const mainTopicCode = mainTopicMatch ? mainTopicMatch[1] : null;
    
    const pageTopics = parseTablePage(markdown, url, mainTopicCode);
    allTopics.push(...pageTopics);
    
    if (pageTopics.length > 0) {
      console.log(`   ${mainTopicCode || url.split('/').pop()}: ${pageTopics.length} topics`);
    }
  }
  
  // Remove duplicates
  const unique = [];
  const seen = new Set();
  
  for (const topic of allTopics) {
    if (!seen.has(topic.code)) {
      unique.push(topic);
      seen.add(topic.code);
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

function parseTablePage(markdown, url, mainTopicCode) {
  const topics = [];
  const lines = markdown.split('\n');
  
  // Level 0: Main topic
  const mainTopicMatch = markdown.match(/^#{1,2}\s+(\d+\.\d+)\s+(.+)$/m);
  if (mainTopicMatch) {
    const code = mainTopicMatch[1];
    const title = mainTopicMatch[2];
    
    topics.push({
      code,
      title: title.trim(),
      level: 0,
      parentCode: null
    });
    
    mainTopicCode = code;
  }
  
  // Parse tables
  let inTable = false;
  let rowCounter = 0;
  
  for (const line of lines) {
    if (line.includes('Content') && line.includes('Additional information')) {
      inTable = true;
      continue;
    }
    
    if (line.match(/^\|?\s*[-:]+\s*\|/)) {
      continue;
    }
    
    if (inTable && line.startsWith('|')) {
      const cells = line.split('|').map(c => c.trim()).filter(c => c);
      
      if (cells.length >= 2 && cells[0].length > 10) {
        rowCounter++;
        
        // Level 1: Content column
        const contentCode = mainTopicCode ? `${mainTopicCode}.${rowCounter}` : `T${rowCounter}`;
        topics.push({
          code: contentCode,
          title: cells[0].replace(/\.$/, '').trim(),
          level: 1,
          parentCode: mainTopicCode
        });
        
        // Level 2: Additional information bullets
        const additionalInfo = cells[1];
        if (additionalInfo && additionalInfo.length > 10) {
          let cleanedInfo = additionalInfo
            .replace(/<br\s*\/?>/gi, '\n')
            .replace(/<[^>]+>/g, '');
          
          const bullets = cleanedInfo
            .split(/\n-\s*|\n•\s*|[•·]\s*/)
            .map(b => b.trim())
            .filter(b => b.length > 5 && !b.match(/^(include|are):$/i));
          
          bullets.forEach((bullet, idx) => {
            const bulletCode = `${contentCode}.${idx + 1}`;
            topics.push({
              code: bulletCode,
              title: bullet.trim().replace(/\.$/, '').replace(/\n/g, ' '),
              level: 2,
              parentCode: contentCode
            });
          });
        }
      }
    }
    
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
  console.log('\n💾 Uploading...');
  
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
    
    await supabase.from('staging_aqa_topics').delete().eq('subject_id', subject.id);
    
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
  } catch (error) {
    console.error('❌ Upload failed:', error);
    throw error;
  }
}

// ================================================================
// MAIN
// ================================================================

async function main() {
  console.log('🚀 BUSINESS');
  console.log('='.repeat(60));
  
  try {
    const pages = await crawlBusiness();
    const topics = parseBusinessTopics(pages);
    await uploadToStaging(topics);
    
    console.log('\n' + '='.repeat(60));
    console.log('✅ BUSINESS COMPLETE!');
    console.log(`   Topics: ${topics.length}`);
    console.log('\nNext: python scrape-business-papers.py');
    
  } catch (error) {
    console.error('\n❌ FAILED:', error.message);
    process.exit(1);
  }
}

main();

