/**
 * AQA BENGALI A-LEVEL Scraper
 * Code: 7637
 * 
 * Structure: Numbered hierarchy (like Biology) with 4 levels
 * 3.1 → 3.1.1 → 3.1.1.1 → bullets
 */

import Firecrawl from '@mendable/firecrawl-js';
import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';

dotenv.config();

const fc = new Firecrawl({ apiKey: process.env.FIRECRAWL_API_KEY });
const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_KEY);

const SUBJECT = {
  name: 'Bengali',
  code: '7637',
  qualification: 'A-Level',
  baseUrl: 'https://www.aqa.org.uk/subjects/bengali/a-level/bengali-7637/specification/subject-content'
};

// ================================================================
// STEP 1: CRAWL
// ================================================================

async function crawlBengali() {
  console.log('🔍 Crawling Bengali...');
  
  try {
    const mapResult = await fc.mapUrl(SUBJECT.baseUrl, {
      includeSubdomains: false,
      limit: 50
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
      console.log(`   [${i + 1}] ${url.split('/').pop()}...`);
      
      try {
        const result = await fc.scrapeUrl(url, {
          formats: ['markdown'],
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
// STEP 2: PARSE (Numbered + Bullets)
// ================================================================

function parseBengaliTopics(pages) {
  console.log('\n📋 Parsing topics...');
  
  const allTopics = [];
  
  for (const page of pages) {
    const markdown = page.markdown || '';
    const pageTopics = parseNumberedAndBullets(markdown);
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

function parseNumberedAndBullets(markdown) {
  const topics = [];
  const lines = markdown.split('\n');
  
  let currentSubThemeCode = null;
  let bulletCounter = 0;
  
  for (const line of lines) {
    // Numbered codes: 3.1, 3.1.1, 3.1.1.1
    const numberedMatch = line.match(/^#{2,6}\s+(\d+(?:\.\d+)+)\s+(.+)$/);
    if (numberedMatch) {
      const code = numberedMatch[1];
      const title = numberedMatch[2].trim();
      const level = code.split('.').length - 2;
      
      topics.push({
        code,
        title,
        level,
        parentCode: level > 0 ? code.split('.').slice(0, -1).join('.') : null
      });
      
      // Track for bullets
      if (level === 2) {  // Sub-themes are level 2 (3.1.1.1)
        currentSubThemeCode = code;
        bulletCounter = 0;
      }
      
      continue;
    }
    
    // Bullets under sub-themes
    const bulletMatch = line.match(/^-\s+[•·]?\s*(.{5,})/);
    if (bulletMatch && currentSubThemeCode) {
      bulletCounter++;
      const bulletCode = `${currentSubThemeCode}.${bulletCounter}`;
      
      topics.push({
        code: bulletCode,
        title: bulletMatch[1].trim(),
        level: 3,
        parentCode: currentSubThemeCode
      });
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
    
    return subject.id;
  } catch (error) {
    console.error('❌ Upload failed:', error);
    throw error;
  }
}

// ================================================================
// MAIN
// ================================================================

async function main() {
  console.log('🚀 BENGALI');
  console.log('='.repeat(60));
  
  try {
    const pages = await crawlBengali();
    const topics = parseBengaliTopics(pages);
    const subjectId = await uploadToStaging(topics);
    
    console.log('\n' + '='.repeat(60));
    console.log('✅ BENGALI COMPLETE!');
    console.log(`   Topics: ${topics.length}`);
    console.log('\nNext: python scrape-bengali-papers.py');
    
  } catch (error) {
    console.error('\n❌ FAILED:', error.message);
    process.exit(1);
  }
}

main();

