/**
 * AQA History A-Level Complete Scraper
 * Code: 7042
 * 
 * History is COMPLEX - has pathway options (1A-1W)
 * Good test of the system!
 */

import Firecrawl from '@mendable/firecrawl-js';
import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';
import fs from 'fs/promises';

dotenv.config();

const fc = new Firecrawl({ apiKey: process.env.FIRECRAWL_API_KEY });
const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_KEY);

// ================================================================
// CONFIG: AQA History
// ================================================================

const SUBJECT = {
  name: 'History',
  code: '7042',
  qualification: 'A-Level',
  baseUrl: 'https://www.aqa.org.uk/subjects/history/a-level/history-7042/specification/subject-content'
};

// ================================================================
// STEP 1: CRAWL ALL HISTORY PAGES
// ================================================================

async function crawlHistoryComplete() {
  console.log('🔍 CRAWLING AQA History...');
  console.log(`   Base URL: ${SUBJECT.baseUrl}`);
  console.log('   This will take 1-2 minutes...\n');
  
  try {
    // Map all pages
    const mapResult = await fc.mapUrl(SUBJECT.baseUrl, {
      includeSubdomains: false,
      limit: 200
    });
    
    const urls = mapResult.links || [];
    console.log(`✅ Found ${urls.length} potential pages`);
    
    // Filter to subject-content pages
    const contentUrls = urls.filter(u => 
      u.includes('/specification/subject-content/') &&
      !u.includes('/downloads/') &&
      !u.includes('/resources/')
    );
    
    console.log(`   Filtered to ${contentUrls.length} content pages`);
    console.log('\n📚 Scraping each page...');
    
    // Scrape each
    const scrapedPages = [];
    
    for (let i = 0; i < contentUrls.length && i < 30; i++) {
      const url = contentUrls[i];
      const pageName = url.split('/').pop() || `page-${i}`;
      
      console.log(`   [${i + 1}/${Math.min(contentUrls.length, 30)}] ${pageName.substring(0, 50)}...`);
      
      try {
        const result = await fc.scrapeUrl(url, {
          formats: ['markdown'],
          onlyMainContent: true
        });
        
        scrapedPages.push({
          ...result,
          metadata: { ...result.metadata, url }
        });
        
      } catch (error) {
        console.warn(`   ⚠️  Failed: ${error.message}`);
      }
    }
    
    console.log(`\n✅ Scraped ${scrapedPages.length} pages`);
    
    // Save for debugging
    await fs.writeFile(
      'debug-history-scraped.json',
      JSON.stringify(scrapedPages.map(p => ({
        url: p.metadata?.url,
        contentLength: p.markdown?.length || 0,
        preview: p.markdown?.substring(0, 200)
      })), null, 2)
    );
    
    return scrapedPages;
  } catch (error) {
    console.error('❌ Crawl failed:', error.message);
    throw error;
  }
}

// ================================================================
// STEP 2: PARSE HISTORY TOPICS
// ================================================================

function parseHistoryTopics(crawledPages) {
  console.log('\n📋 Parsing History topics...');
  
  const allTopics = [];
  
  for (const page of crawledPages) {
    const markdown = page.markdown || '';
    const url = page.metadata?.url || '';
    
    const pageTopics = extractHistoryTopics(markdown, url);
    allTopics.push(...pageTopics);
  }
  
  // Build hierarchy and remove duplicates
  const hierarchical = buildHierarchy(allTopics);
  
  console.log(`✅ Parsed ${hierarchical.length} unique topics`);
  
  // Show distribution
  const levels = {};
  hierarchical.forEach(t => levels[t.level] = (levels[t.level] || 0) + 1);
  
  console.log('   Distribution:');
  Object.keys(levels).sort().forEach(l => {
    console.log(`   Level ${l}: ${levels[l]} topics`);
  });
  
  // Show pathway options
  const pathways = hierarchical.filter(t => t.code.match(/^\d+[A-Z]$/));
  console.log(`   Pathway options: ${pathways.length} (e.g., 1A, 1B, 2A...)`);
  
  return hierarchical;
}

function extractHistoryTopics(markdown, sourceUrl) {
  const topics = [];
  const lines = markdown.split('\n');
  
  // History patterns:
  const patterns = [
    // Option codes: 1A, 1B, 2A, 2B, etc.
    { regex: /^-\s*[•·]\s*\[(\d+[A-Z])\s+([^\]]+)\]/, type: 'option_bullet' },
    { regex: /^(#{2,6})\s+(\d+[A-Z])\s+(.+)$/, type: 'option_heading' },
    
    // Component numbers: 1, 2, 3
    { regex: /^(#{2,3})\s+(\d+\.\d+)\s+(.+)$/, type: 'component' },
    
    // Standard numbered: 3.1, 3.1.1
    { regex: /^-\s*[•·]\s*\[(\d+(?:\.\d+)+)\s+([^\]]+)\]/, type: 'numbered_bullet' },
    { regex: /^(#{2,6})\s+(\d+(?:\.\d+)+)\s+(.+)$/, type: 'numbered_heading' }
  ];
  
  for (const line of lines) {
    for (const pattern of patterns) {
      const match = line.match(pattern.regex);
      
      if (match) {
        let code, title, level;
        
        if (pattern.type.includes('heading')) {
          const headingLevel = match[1].length;
          code = match[2];
          title = match[3];
          level = headingLevel - 1;
        } else if (pattern.type.includes('bullet')) {
          code = match[1];
          title = match[2];
          level = code.split('.').length - 2;
          if (level < 0) level = 0;
        }
        
        if (code && title) {
          topics.push({
            code,
            title: title.trim(),
            level,
            sourceUrl,
            patternType: pattern.type
          });
          break;
        }
      }
    }
  }
  
  return topics;
}

function buildHierarchy(topics) {
  const hierarchical = topics.map(topic => {
    let parentCode = null;
    
    // Option codes (1A, 2B) don't have parents from code structure
    if (topic.code.match(/^\d+[A-Z]$/)) {
      // Extract component number (1A → parent is "1")
      parentCode = topic.code.substring(0, 1);
    } else {
      // Standard numbered codes (3.1.1 → parent is 3.1)
      const parts = topic.code.split('.');
      if (parts.length > 1) {
        parentCode = parts.slice(0, -1).join('.');
      }
    }
    
    return { ...topic, parentCode };
  });
  
  // Remove duplicates
  const unique = [];
  const seen = new Set();
  
  for (const topic of hierarchical) {
    if (!seen.has(topic.code)) {
      unique.push(topic);
      seen.add(topic.code);
    }
  }
  
  return unique;
}

// ================================================================
// STEP 3: UPLOAD TO STAGING
// ================================================================

async function uploadToStaging(topics) {
  console.log('\n💾 Uploading to staging database...');
  
  try {
    // 1. Subject
    const { data: subject, error: subjectError } = await supabase
      .from('staging_aqa_subjects')
      .upsert({
        subject_name: `${SUBJECT.name} (${SUBJECT.qualification})`,
        subject_code: SUBJECT.code,
        qualification_type: SUBJECT.qualification,
        specification_url: SUBJECT.baseUrl
      }, { onConflict: 'subject_code,qualification_type' })
      .select()
      .single();
    
    if (subjectError) throw subjectError;
    console.log(`✅ Subject: ${subject.subject_name}`);
    
    // 2. DELETE old topics (prevents duplicates!)
    await supabase
      .from('staging_aqa_topics')
      .delete()
      .eq('subject_id', subject.id);
    
    console.log(`✅ Cleared old topics (prevents duplicates)`);
    
    // 3. Insert topics
    const topicsToInsert = topics.map(t => ({
      subject_id: subject.id,
      topic_code: t.code,
      topic_name: t.title,
      topic_level: t.level
    }));
    
    const { data: insertedTopics } = await supabase
      .from('staging_aqa_topics')
      .insert(topicsToInsert)
      .select();
    
    console.log(`✅ Uploaded ${insertedTopics.length} topics`);
    
    // 4. Link hierarchy
    const codeToId = new Map(insertedTopics.map(t => [t.topic_code, t.id]));
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
    
    console.log(`✅ Linked ${linked} parent-child relationships`);
    
    return subject.id;
  } catch (error) {
    console.error('❌ Upload failed:', error);
    throw error;
  }
}

// ================================================================
// STEP 4: VALIDATION
// ================================================================

async function validateData(subjectId) {
  console.log('\n📊 Validating History dataset...');
  
  const { data: allTopics } = await supabase
    .from('staging_aqa_topics')
    .select('*')
    .eq('subject_id', subjectId)
    .order('topic_code');
  
  // Count by level
  const levels = {};
  allTopics.forEach(t => levels[t.topic_level] = (levels[t.topic_level] || 0) + 1);
  
  console.log(`   Total topics: ${allTopics.length}`);
  Object.keys(levels).sort().forEach(l => {
    console.log(`   Level ${l}: ${levels[l]} topics`);
  });
  
  // Check for pathway options
  const pathwayOptions = allTopics.filter(t => t.topic_code.match(/^\d+[A-Z]$/));
  console.log(`   Pathway options (1A, 1B, etc.): ${pathwayOptions.length}`);
  
  // Sample
  console.log('\n📋 Sample topics (first 20):');
  allTopics.slice(0, 20).forEach(t => {
    const indent = '  '.repeat(t.topic_level);
    console.log(`   ${indent}${t.topic_code} - ${t.topic_name}`);
  });
  
  return allTopics.length;
}

// ================================================================
// MAIN
// ================================================================

async function main() {
  console.log('🚀 AQA HISTORY COMPLETE CRAWL');
  console.log('='.repeat(60));
  
  try {
    // Step 1: Crawl
    const pages = await crawlHistoryComplete();
    
    // Step 2: Parse
    const topics = parseHistoryTopics(pages);
    
    // Step 3: Upload (REPLACES old data - no duplicates!)
    const subjectId = await uploadToStaging(topics);
    
    // Step 4: Validate
    const totalCount = await validateData(subjectId);
    
    console.log('\n' + '='.repeat(60));
    console.log('✅ HISTORY CRAWL SUCCESSFUL!');
    console.log(`   Total topics: ${totalCount}`);
    console.log('\n💡 Notes:');
    console.log('   - Pathway options (1A-1W) extracted');
    console.log('   - Can be re-run safely (deletes old data first)');
    console.log('   - No duplicates will occur!');
    console.log('\nNext: Run the papers scraper for History');
    
  } catch (error) {
    console.error('\n❌ FAILED:', error.message);
    console.error(error.stack);
    process.exit(1);
  }
}

main();

