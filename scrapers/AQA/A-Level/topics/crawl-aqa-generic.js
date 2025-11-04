/**
 * GENERIC AQA Subject Crawler
 * 
 * Works for ANY AQA A-Level subject
 * Configure via command line or config file
 * 
 * Usage:
 *   node crawl-aqa-generic.js Biology 7402
 *   node crawl-aqa-generic.js History 7042
 *   node crawl-aqa-generic.js Chemistry 7405
 */

import Firecrawl from '@mendable/firecrawl-js';
import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';
import fs from 'fs/promises';

dotenv.config();

const fc = new Firecrawl({ apiKey: process.env.FIRECRAWL_API_KEY });
const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_KEY);

// ================================================================
// GET SUBJECT FROM COMMAND LINE OR CONFIG
// ================================================================

let SUBJECT;

if (process.argv.length >= 4) {
  // Command line: node crawl-aqa-generic.js History 7042
  const name = process.argv[2];
  const code = process.argv[3];
  const slug = name.toLowerCase().replace(/ /g, '-');
  
  SUBJECT = {
    name,
    code,
    qualification: 'A-Level',
    baseUrl: `https://www.aqa.org.uk/subjects/${slug}/a-level/${slug}-${code}/specification/subject-content`
  };
} else {
  console.error('Usage: node crawl-aqa-generic.js <SubjectName> <Code>');
  console.error('Example: node crawl-aqa-generic.js History 7042');
  process.exit(1);
}

// ================================================================
// STEP 1: CRAWL
// ================================================================

async function crawlSubject() {
  console.log(`🔍 Crawling ${SUBJECT.name}...`);
  console.log(`   URL: ${SUBJECT.baseUrl}`);
  
  try {
    // Map pages
    const mapResult = await fc.mapUrl(SUBJECT.baseUrl, {
      includeSubdomains: false,
      limit: 200
    });
    
    const urls = mapResult.links || [];
    console.log(`✅ Found ${urls.length} pages`);
    
    // Filter content pages
    const contentUrls = urls.filter(u => 
      u.includes('/specification/subject-content/') &&
      !u.includes('/downloads/')
    );
    
    console.log(`   Content pages: ${contentUrls.length}`);
    
    // Scrape each
    const scrapedPages = [];
    for (let i = 0; i < Math.min(contentUrls.length, 25); i++) {
      const url = contentUrls[i];
      console.log(`   [${i + 1}] ${url.split('/').pop().substring(0, 40)}...`);
      
      try {
        const result = await fc.scrapeUrl(url, {
          formats: ['markdown'],
          onlyMainContent: true
        });
        scrapedPages.push({ ...result, metadata: { url } });
      } catch (err) {
        console.warn(`   ⚠️  Failed`);
      }
    }
    
    console.log(`\n✅ Scraped ${scrapedPages.length} pages`);
    return scrapedPages;
    
  } catch (error) {
    console.error('❌ Crawl failed:', error.message);
    throw error;
  }
}

// ================================================================
// STEP 2: PARSE (Generic patterns)
// ================================================================

function parseTopics(pages) {
  console.log('\n📋 Parsing topics...');
  
  const allTopics = [];
  
  for (const page of pages) {
    const markdown = page.markdown || '';
    const pageTopics = extractTopics(markdown);
    allTopics.push(...pageTopics);
  }
  
  const hierarchical = buildHierarchy(allTopics);
  
  console.log(`✅ Found ${hierarchical.length} unique topics`);
  
  const levels = {};
  hierarchical.forEach(t => levels[t.level] = (levels[t.level] || 0) + 1);
  Object.keys(levels).sort().forEach(l => {
    console.log(`   Level ${l}: ${levels[l]} topics`);
  });
  
  return hierarchical;
}

function extractTopics(markdown) {
  const topics = [];
  const lines = markdown.split('\n');
  
  // ALL known AQA patterns
  const patterns = [
    // Bullet lists: - • [3.1 Topic](url) or - • [1A Option](url)
    { regex: /^-\s*[•·]\s*\[(\d+(?:\.\d+)*|\d+[A-Z])\s+([^\]]+)\]/, type: 'bullet' },
    
    // Headings: ## 3.1 Topic or ### 3.1.1 Subtopic or ## 1A Option
    { regex: /^(#{2,6})\s+(\d+(?:\.\d+)*|\d+[A-Z]|[A-S]:)\s+(.+)$/, type: 'heading' },
    
    // Plain numbered: 3.1.1 Topic name (at start of line)
    { regex: /^(\d+(?:\.\d+)+)\s+([A-Z][^.]{3,})$/, type: 'plain' }
  ];
  
  for (const line of lines) {
    for (const pattern of patterns) {
      const match = line.match(pattern.regex);
      
      if (match) {
        let code, title, level;
        
        if (pattern.type === 'heading') {
          code = match[2];
          title = match[3];
          level = match[1].length - 1;
        } else {
          code = match[1];
          title = match[2];
          // Calculate level from code structure
          if (code.match(/^\d+[A-Z]$/)) {
            level = 0; // Pathway options are top-level
          } else if (code.match(/^[A-S]:$/)) {
            level = 0; // Maths sections are top-level
          } else {
            level = code.split('.').length - 2;
            if (level < 0) level = 0;
          }
        }
        
        if (code && title) {
          topics.push({
            code: code.replace(':', ''), // Remove trailing colons
            title: title.trim(),
            level
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
    
    // Option codes (1A, 2B) - parent is the component number
    if (topic.code.match(/^\d+[A-Z]$/)) {
      parentCode = topic.code.substring(0, 1);
    }
    // Lettered (A, B, C for Maths) - no parent
    else if (topic.code.match(/^[A-S]$/)) {
      parentCode = null;
    }
    // Numbered (3.1.1 → parent is 3.1)
    else {
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
// STEP 3: UPLOAD (DELETES old data first - NO DUPLICATES!)
// ================================================================

async function uploadToStaging(topics) {
  console.log('\n💾 Uploading to staging database...');
  
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
    
    // 2. DELETE OLD TOPICS - This prevents duplicates!
    const { count } = await supabase
      .from('staging_aqa_topics')
      .delete()
      .eq('subject_id', subject.id);
    
    if (count > 0) {
      console.log(`✅ Deleted ${count} old topics (prevents duplicates)`);
    }
    
    // 3. Insert new topics
    const topicsToInsert = topics.map(t => ({
      subject_id: subject.id,
      topic_code: t.code,
      topic_name: t.title,
      topic_level: t.level
    }));
    
    const { data: inserted } = await supabase
      .from('staging_aqa_topics')
      .insert(topicsToInsert)
      .select();
    
    console.log(`✅ Uploaded ${inserted.length} topics`);
    
    // 4. Link hierarchy
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
// STEP 4: VALIDATION
// ================================================================

async function validate(subjectId) {
  console.log('\n📊 Validation...');
  
  const { data: topics } = await supabase
    .from('staging_aqa_topics')
    .select('*')
    .eq('subject_id', subjectId)
    .order('topic_code');
  
  console.log(`   Total topics: ${topics.length}`);
  
  console.log('\n📋 First 15 topics:');
  topics.slice(0, 15).forEach(t => {
    const indent = '  '.repeat(t.topic_level);
    console.log(`   ${indent}${t.topic_code} ${t.topic_name}`);
  });
}

// ================================================================
// MAIN
// ================================================================

async function main() {
  console.log(`🚀 ${SUBJECT.name.toUpperCase()} (${SUBJECT.code})`);
  console.log('='.repeat(60));
  
  try {
    const pages = await crawlSubject();
    const topics = parseTopics(pages);
    const subjectId = await uploadToStaging(topics);
    await validate(subjectId);
    
    console.log('\n' + '='.repeat(60));
    console.log('✅ SUCCESS!');
    console.log('\n💡 DUPLICATE SAFETY:');
    console.log('   Re-run this script 10 times - it will ALWAYS');
    console.log('   have the same number of topics (no duplicates!)');
    
  } catch (error) {
    console.error('\n❌ FAILED:', error.message);
    process.exit(1);
  }
}

main();

