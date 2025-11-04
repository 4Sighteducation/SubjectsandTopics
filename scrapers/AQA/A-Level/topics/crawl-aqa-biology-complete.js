/**
 * COMPLETE AQA Subject Crawl - Gets ALL Subtopics
 * 
 * Uses Firecrawl to follow links and get full hierarchy
 * Works for ANY AQA subject - just change config below
 */

import Firecrawl from '@mendable/firecrawl-js';
import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';

dotenv.config();

const FIRECRAWL_API_KEY = process.env.FIRECRAWL_API_KEY;
const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_SERVICE_KEY = process.env.SUPABASE_SERVICE_KEY;

const fc = new Firecrawl({ apiKey: FIRECRAWL_API_KEY });
const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY);

// ================================================================
// CONFIG: AQA Biology
// ================================================================

const SUBJECT = {
  name: 'History',
  code: '7042',
  qualification: 'A-Level',
  baseUrl: 'https://www.aqa.org.uk/subjects/history/a-level/history-7042/specification/subject-content'
};

// ================================================================
// STEP 1: CRAWL (Follow all links to get full hierarchy)
// ================================================================

async function crawlBiologyComplete() {
  console.log('🔍 Step 1: Finding all Biology pages...');
  
  try {
    // First, map to find all section URLs
    const mapResult = await fc.mapUrl(SUBJECT.baseUrl, {
      search: 'biology 7402 specification',
      includeSubdomains: false,
      limit: 100
    });
    
    const urls = mapResult.links || [];
    console.log(`✅ Found ${urls.length} potential pages`);
    
    // Filter to only specification/subject-content pages
    const contentUrls = urls.filter(url => 
      url.includes('/specification/subject-content/') &&
      !url.includes('/downloads/') &&
      !url.includes('/resources/')
    );
    
    console.log(`   Filtered to ${contentUrls.length} content pages`);
    console.log('\n🔍 Step 2: Scraping each page...');
    
    // Scrape each URL individually
    const scrapedPages = [];
    
    for (let i = 0; i < contentUrls.length; i++) {
      const url = contentUrls[i];
      const pageName = url.split('/').pop() || `page-${i}`;
      
      console.log(`   [${i + 1}/${contentUrls.length}] ${pageName}...`);
      
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
        console.warn(`   ⚠️  Failed to scrape ${url}: ${error.message}`);
      }
    }
    
    console.log(`\n✅ Scraped ${scrapedPages.length} pages successfully`);
    
    return scrapedPages;
  } catch (error) {
    console.error('❌ Crawl failed:', error.message);
    throw error;
  }
}

// ================================================================
// STEP 2: PARSE ALL PAGES
// ================================================================

function parseAllTopics(crawledPages) {
  console.log('\n📋 Parsing topics from all pages...');
  
  const allTopics = [];
  
  for (const page of crawledPages) {
    const url = page.metadata?.url || page.metadata?.sourceURL || '';
    const markdown = page.markdown || '';
    
    console.log(`   Processing: ${url.split('/').pop() || 'index'}`);
    
    const pageTopics = parseMarkdownPage(markdown, url);
    allTopics.push(...pageTopics);
  }
  
  console.log(`\n✅ Total topics found: ${allTopics.length}`);
  
  // Show distribution
  const levels = {};
  allTopics.forEach(t => {
    levels[t.level] = (levels[t.level] || 0) + 1;
  });
  
  console.log('   Distribution by level:');
  Object.keys(levels).sort().forEach(level => {
    console.log(`   - Level ${level}: ${levels[level]} topics`);
  });
  
  return allTopics;
}

function parseMarkdownPage(markdown, sourceUrl) {
  const topics = [];
  const lines = markdown.split('\n');
  
  // Multiple patterns AQA uses:
  const patterns = [
    // Bullet list: - • [3.1 Topic](url)
    { regex: /^-\s*[•·]\s*\[(\d+(?:\.\d+)*)\s+([^\]]+)\]/, type: 'bullet' },
    
    // Heading: ## 3.1 Topic or ### 3.1.1 Subtopic
    { regex: /^(#{2,6})\s+(\d+(?:\.\d+)*)\s+(.+)$/, type: 'heading' },
    
    // Table row: 3.1.1 | Topic name
    { regex: /^\|?\s*(\d+(?:\.\d+)+)\s*\|?\s*(.+)$/, type: 'table' },
    
    // Plain numbered list: 3.1.1 Topic name
    { regex: /^(\d+(?:\.\d+)+)\s+([A-Z].+)$/, type: 'plain' }
  ];
  
  for (const line of lines) {
    for (const pattern of patterns) {
      const match = line.match(pattern.regex);
      
      if (match) {
        let code, title, level;
        
        if (pattern.type === 'heading') {
          const headingLevel = match[1].length; // ## = 2, ### = 3
          code = match[2];
          title = match[3];
        } else if (pattern.type === 'bullet' || pattern.type === 'table' || pattern.type === 'plain') {
          code = match[1];
          title = match[2];
        }
        
        if (code && title) {
          // Calculate level from code depth (3.1 = 0, 3.1.1 = 1, 3.1.1.1 = 2)
          level = code.split('.').length - 2;
          if (level < 0) level = 0;
          
          // Check for A-level only flag
          const isALevelOnly = title.toLowerCase().includes('(a-level only)');
          const cleanTitle = title.replace(/\(A-level only\)/gi, '').trim();
          
          topics.push({
            code,
            title: cleanTitle,
            level,
            isALevelOnly,
            sourceUrl,
            patternType: pattern.type
          });
          
          break; // Found a match, move to next line
        }
      }
    }
  }
  
  return topics;
}

// ================================================================
// STEP 3: BUILD HIERARCHY
// ================================================================

function buildHierarchy(topics) {
  console.log('\n🌳 Building topic hierarchy...');
  
  const hierarchicalTopics = topics.map(topic => {
    // Find parent code (e.g., 3.1.1 → parent is 3.1)
    const codeParts = topic.code.split('.');
    const parentCode = codeParts.length > 1 
      ? codeParts.slice(0, -1).join('.')
      : null;
    
    return {
      ...topic,
      parentCode
    };
  });
  
  // Remove duplicates (same code might appear on multiple pages)
  const uniqueTopics = [];
  const seen = new Set();
  
  for (const topic of hierarchicalTopics) {
    if (!seen.has(topic.code)) {
      uniqueTopics.push(topic);
      seen.add(topic.code);
    }
  }
  
  console.log(`✅ Hierarchy built with ${uniqueTopics.length} unique topics`);
  
  // Count levels
  const topLevel = uniqueTopics.filter(t => !t.parentCode);
  console.log(`   Top-level sections: ${topLevel.length} (expected: 7-8)`);
  
  return uniqueTopics;
}

// ================================================================
// STEP 4: UPLOAD TO STAGING
// ================================================================

async function uploadToStaging(topics) {
  console.log('\n💾 Uploading to staging database...');
  
  try {
    // 1. Insert subject
    const { data: subject, error: subjectError } = await supabase
      .from('staging_aqa_subjects')
      .upsert({
        subject_name: `${SUBJECT.name} (${SUBJECT.qualification})`,
        subject_code: SUBJECT.code,
        qualification_type: SUBJECT.qualification,
        specification_url: SUBJECT.baseUrl
      }, {
        onConflict: 'subject_code,qualification_type'
      })
      .select()
      .single();
    
    if (subjectError) throw subjectError;
    console.log(`✅ Subject: ${subject.subject_name}`);
    
    // 2. Clear old topics
    await supabase
      .from('staging_aqa_topics')
      .delete()
      .eq('subject_id', subject.id);
    
    // 3. Insert all topics (first pass - no parents)
    const topicsToInsert = topics.map(topic => ({
      subject_id: subject.id,
      topic_code: topic.code,
      topic_name: topic.title,
      topic_level: topic.level,
      is_a_level_only: topic.isALevelOnly
    }));
    
    const { data: insertedTopics, error: topicsError } = await supabase
      .from('staging_aqa_topics')
      .insert(topicsToInsert)
      .select();
    
    if (topicsError) throw topicsError;
    console.log(`✅ Uploaded ${insertedTopics.length} topics`);
    
    // 4. Link parent-child relationships (second pass)
    console.log('🔗 Linking hierarchy...');
    
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
    console.error('❌ Upload failed:', error.message);
    throw error;
  }
}

// ================================================================
// STEP 5: VALIDATION
// ================================================================

async function validateData(subjectId) {
  console.log('\n📊 Validating complete dataset...');
  
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
  
  // Check A-level only flags
  const aLevelOnly = allTopics.filter(t => t.is_a_level_only);
  console.log(`   A-level only topics: ${aLevelOnly.length}`);
  
  // Sample hierarchy
  console.log('\n📋 Sample hierarchy:');
  allTopics.slice(0, 15).forEach(t => {
    const indent = '  '.repeat(t.topic_level);
    console.log(`   ${indent}${t.topic_code} - ${t.topic_name}`);
  });
  
  return allTopics.length;
}

// ================================================================
// MAIN
// ================================================================

async function main() {
  console.log('🚀 AQA Biology COMPLETE Crawl');
  console.log('='.repeat(60));
  
  try {
    // Step 1: Crawl all pages
    const pages = await crawlBiologyComplete();
    
    // Step 2: Parse all topics from all pages
    const allTopics = parseAllTopics(pages);
    
    // Step 3: Build hierarchy
    const hierarchicalTopics = buildHierarchy(allTopics);
    
    // Step 4: Upload to staging
    const subjectId = await uploadToStaging(hierarchicalTopics);
    
    // Step 5: Validate
    const totalCount = await validateData(subjectId);
    
    console.log('\n' + '='.repeat(60));
    console.log('✅ COMPLETE CRAWL SUCCESSFUL!');
    console.log(`   Total topics scraped: ${totalCount}`);
    console.log(`   Expected for Biology: 60-100 topics with full hierarchy`);
    console.log('\nNext: Check Supabase staging_aqa_topics to see the full hierarchy!');
    
  } catch (error) {
    console.error('\n❌ CRAWL FAILED:', error.message);
    console.error(error.stack);
    process.exit(1);
  }
}

main();

