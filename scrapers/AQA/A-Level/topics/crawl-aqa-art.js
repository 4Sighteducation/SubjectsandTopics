/**
 * AQA ART AND DESIGN A-LEVEL Scraper
 * Codes: 7201-7207 (7 different pathways)
 * 
 * Structure:
 * Level 0: Main sections (Areas of study, Skills, Knowledge)
 * Level 1: Bullet points under each
 * 
 * Run this 7 times with different codes:
 * node crawl-aqa-art.js "Fine art" 7202
 * node crawl-aqa-art.js "Photography" 7206
 * etc.
 */

import Firecrawl from '@mendable/firecrawl-js';
import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';

dotenv.config();

const fc = new Firecrawl({ apiKey: process.env.FIRECRAWL_API_KEY });
const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_KEY);

// ================================================================
// CONFIG FROM COMMAND LINE
// ================================================================

// No command line args needed - Art is ONE subject with all pathways

// Art and Design = ONE subject with multiple pathways
const SUBJECT = {
  name: 'Art and Design',
  code: '7201',  // Use base code
  qualification: 'A-Level',
  baseUrl: 'https://www.aqa.org.uk/subjects/art-and-design/a-level/art-and-design-7202/specification/subject-content'  // Any code works, they share content
};

// ================================================================
// STEP 1: CRAWL
// ================================================================

async function crawlArt() {
  console.log(`🔍 Crawling ${SUBJECT.name}...`);
  console.log(`   Code: ${SUBJECT.code}`);
  
  try {
    // Map to find sub-pages
    const mapResult = await fc.mapUrl(SUBJECT.baseUrl, {
      includeSubdomains: false,
      limit: 50
    });
    
    const urls = mapResult.links || [];
    const contentUrls = urls.filter(u => 
      u.includes('/specification/subject-content/') &&
      !u.includes('/downloads/') &&
      u !== SUBJECT.baseUrl  // Exclude the index page itself
    );
    
    console.log(`✅ Found ${contentUrls.length} sub-pages`);
    console.log('\n📚 Scraping pages...');
    
    const pages = [];
    for (let i = 0; i < contentUrls.length; i++) {
      const url = contentUrls[i];
      console.log(`   [${i + 1}/${contentUrls.length}] ${url.split('/').pop()}...`);
      
      try {
        const result = await fc.scrapeUrl(url, {
          formats: ['markdown'],
          onlyMainContent: true
        });
        pages.push({ ...result, url });
        
        // Save first page for debugging
        if (i === 0) {
          await import('fs/promises').then(fs => 
            fs.writeFile('debug-art-page.md', result.markdown || '')
          );
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
// STEP 2: PARSE ART STRUCTURE
// ================================================================

function parseArtTopics(pages) {
  console.log('\n📋 Parsing Art topics...');
  
  const allTopics = [];
  
  for (const page of pages) {
    const markdown = page.markdown || '';
    const url = page.url || '';
    const pageTopics = parseArtPage(markdown, url);
    allTopics.push(...pageTopics);
  }
  
  console.log(`✅ Found ${allTopics.length} topics`);
  
  const levels = {};
  allTopics.forEach(t => levels[t.level] = (levels[t.level] || 0) + 1);
  Object.keys(levels).sort().forEach(l => {
    console.log(`   Level ${l}: ${levels[l]} topics`);
  });
  
  return allTopics;
}

function parseArtPage(markdown, url) {
  const topics = [];
  const lines = markdown.split('\n');
  
  // Extract pathway from URL (3.3, 3.4, 3.5, etc.)
  const pathwayMatch = url.match(/\/(\d+\.\d+)-/) || markdown.match(/^#{1,2}\s+(\d+\.\d+)\s+/m);
  const pathwayCode = pathwayMatch ? pathwayMatch[1] : null;
  
  // Skip 3.1 and 3.2 (general content as you said)
  if (pathwayCode && (pathwayCode === '3.1' || pathwayCode === '3.2')) {
    return topics;  // Skip these pages
  }
  
  // Level 0: Pathway itself (3.3 Art craft and design, 3.4 Fine art, etc.)
  const pathwayTitle = markdown.match(/^#{1,2}\s+\d+\.\d+\s+(.+)$/m);
  if (pathwayCode && pathwayTitle) {
    topics.push({
      code: pathwayCode,
      title: pathwayTitle[1].trim(),
      level: 0,
      parentCode: null
    });
  }
  
  let currentSection = null;
  let currentSectionCode = null;
  let sectionCounter = 0;
  let bulletCounter = 0;
  
  for (const line of lines) {
    // Level 1: Main sections (## Areas of study, ## Skills and techniques, ## Knowledge and understanding)
    const sectionMatch = line.match(/^#{2,3}\s+(Areas?\s+of\s+study|Skills?\s+(and\s+)?techniques?|Knowledge\s+and\s+understanding)/i);
    
    if (sectionMatch) {
      sectionCounter++;
      bulletCounter = 0;
      
      currentSection = sectionMatch[1];
      currentSectionCode = pathwayCode ? `${pathwayCode}.S${sectionCounter}` : `S${sectionCounter}`;
      
      topics.push({
        code: currentSectionCode,
        title: currentSection,
        level: 1,
        parentCode: pathwayCode
      });
      continue;
    }
    
    // Level 2: Bullet points under sections
    const bulletMatch = line.match(/^-\s+(.{5,})/);
    if (bulletMatch && currentSectionCode) {
      bulletCounter++;
      const bulletCode = `${currentSectionCode}.${bulletCounter}`;
      
      topics.push({
        code: bulletCode,
        title: bulletMatch[1].trim(),
        level: 2,
        parentCode: currentSectionCode
      });
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
        subject_name: SUBJECT.name,
        subject_code: SUBJECT.code,
        qualification_type: SUBJECT.qualification,
        specification_url: SUBJECT.baseUrl
      }, { onConflict: 'subject_code,qualification_type' })
      .select()
      .single();
    
    console.log(`✅ Subject: ${subject.subject_name}`);
    
    await supabase.from('staging_aqa_topics').delete().eq('subject_id', subject.id);
    console.log(`✅ Cleared old topics`);
    
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
  
  console.log(`   Total: ${topics.length}`);
  
  console.log('\n📋 All topics:');
  topics.forEach(t => {
    const indent = '  '.repeat(t.topic_level);
    console.log(`   ${indent}${t.topic_code} ${t.topic_name}`);
  });
}

// ================================================================
// MAIN
// ================================================================

async function main() {
  console.log(`🚀 ${SUBJECT.name.toUpperCase()}`);
  console.log('='.repeat(60));
  
  try {
    const pages = await crawlArt();
    const topics = parseArtTopics(pages);
    const subjectId = await uploadToStaging(topics);
    await validate(subjectId);
    
    console.log('\n' + '='.repeat(60));
    console.log('✅ COMPLETE!');
    console.log(`\n${SUBJECT.name}: ${topics.length} topics`);
    
  } catch (error) {
    console.error('\n❌ FAILED:', error.message);
    process.exit(1);
  }
}

main();

