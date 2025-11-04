/**
 * AQA COMPUTER SCIENCE A-LEVEL Scraper
 * Code: 7517
 * 
 * Structure: 4.X numbered hierarchy + tables (4 levels)
 * 4.1 → 4.1.1 → 4.1.1.1 → Table bullets
 */

import Firecrawl from '@mendable/firecrawl-js';
import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';

dotenv.config();

const fc = new Firecrawl({ apiKey: process.env.FIRECRAWL_API_KEY });
const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_KEY);

const SUBJECT = {
  name: 'Computer Science',
  code: '7517',
  qualification: 'A-Level',
  baseUrl: 'https://www.aqa.org.uk/subjects/computer-science/a-level/computer-science-7517/specification'
};

// ================================================================
// STEP 1: CRAWL
// ================================================================

async function crawlComputerScience() {
  console.log('🔍 Crawling Computer Science...');
  
  try {
    const mapResult = await fc.mapUrl(SUBJECT.baseUrl, {
      includeSubdomains: false,
      limit: 100
    });
    
    const urls = mapResult.links || [];
    const contentUrls = urls.filter(u => 
      (u.includes('/fundamentals-of-') || 
       u.includes('/theory-of-') ||
       u.includes('/big-data') ||
       u.includes('/subject-content-a-level')) &&
      !u.includes('/downloads/') &&
      !u.includes('sitemap')
    );
    
    console.log(`✅ Found ${contentUrls.length} content pages`);
    console.log('\n📚 Scraping pages...');
    
    const pages = [];
    for (let i = 0; i < Math.min(contentUrls.length, 20); i++) {
      const url = contentUrls[i];
      console.log(`   [${i + 1}] ${url.split('/').pop().substring(0, 40)}...`);
      
      try {
        const result = await fc.scrapeUrl(url, {
          formats: ['markdown'],
          onlyMainContent: true
        });
        pages.push({ ...result, url });
        
        // Save first page for debugging
        if (i === 0) {
          await import('fs/promises').then(fs => 
            fs.writeFile('debug-cs-page.md', result.markdown || '')
          );
          console.log(`   💾 Saved debug-cs-page.md`);
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
// STEP 2: PARSE (Same as Chemistry, just 4.X instead of 3.X)
// ================================================================

function parseComputerScienceTopics(pages) {
  console.log('\n📋 Parsing Computer Science topics...');
  
  const allTopics = [];
  
  for (const page of pages) {
    const markdown = page.markdown || '';
    const pageTopics = parseNumberedWithTables(markdown);
    allTopics.push(...pageTopics);
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
  
  console.log(`✅ Found ${unique.length} unique topics`);
  
  const levels = {};
  unique.forEach(t => levels[t.level] = (levels[t.level] || 0) + 1);
  Object.keys(levels).sort().forEach(l => {
    console.log(`   Level ${l}: ${levels[l]} topics`);
  });
  
  return unique;
}

function parseNumberedWithTables(markdown) {
  const topics = [];
  const lines = markdown.split('\n');
  
  let currentLevel2Code = null;
  let inTable = false;
  let bulletCounter = 0;
  
  for (const line of lines) {
    // Numbered headings: 4.1, 4.1.1, 4.1.1.1
    const numberedMatch = line.match(/^(#{2,6})\s+(\d+(?:\.\d+)+)\s+(.+)$/);
    if (numberedMatch) {
      const code = numberedMatch[2];
      const title = numberedMatch[3].trim();
      const level = code.split('.').length - 2;
      
      topics.push({
        code,
        title,
        level,
        parentCode: level > 0 ? code.split('.').slice(0, -1).join('.') : null
      });
      
      // Track Level 2 (4.1.1.1) for table bullets
      if (level === 2) {
        currentLevel2Code = code;
        bulletCounter = 0;
      }
      
      continue;
    }
    
    // Table start
    if (line.includes('Content') && (line.includes('Additional') || line.includes('information'))) {
      inTable = true;
      continue;
    }
    
    // Table separator
    if (line.match(/^\|?\s*[-:]+\s*\|/)) {
      continue;
    }
    
    // Table rows → Level 3 bullets
    if (inTable && line.startsWith('|') && currentLevel2Code) {
      const cells = line.split('|').map(c => c.trim()).filter(c => c);
      
      if (cells.length >= 1 && cells[0].length > 5) {
        // Extract bullets from Content cell
        let content = cells[0]
          .replace(/<br\s*\/?>/gi, '\n')
          .replace(/<[^>]+>/g, '');
        
        // Split on bullet markers
        const contentLines = content
          .split(/\n[•·-]\s*/)
          .filter(l => l.trim().length > 5)
          .map(l => l.trim());
        
        contentLines.forEach((line, idx) => {
          bulletCounter++;
          const bulletCode = `${currentLevel2Code}.${bulletCounter}`;
          
          topics.push({
            code: bulletCode,
            title: line,
            level: 3,
            parentCode: currentLevel2Code
          });
        });
      }
    }
    
    // Exit table
    if (inTable && line.match(/^#{1,6}\s+/)) {
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
  console.log('🚀 COMPUTER SCIENCE');
  console.log('='.repeat(60));
  
  try {
    const pages = await crawlComputerScience();
    const topics = parseComputerScienceTopics(pages);
    await uploadToStaging(topics);
    
    console.log('\n' + '='.repeat(60));
    console.log('✅ COMPUTER SCIENCE COMPLETE!');
    console.log(`   Topics: ${topics.length}`);
    console.log('\nNext: python scrape-computer-science-papers.py');
    
  } catch (error) {
    console.error('\n❌ FAILED:', error.message);
    process.exit(1);
  }
}

main();

