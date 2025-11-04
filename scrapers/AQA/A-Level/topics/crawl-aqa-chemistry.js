/**
 * AQA CHEMISTRY A-LEVEL Scraper
 * Code: 7405
 * 
 * Structure: Numbered hierarchy (like Biology but 4 levels deep)
 * 3.1 → 3.1.1 → 3.1.1.1 → Table content
 * Also has tables with Content | Opportunities columns
 */

import Firecrawl from '@mendable/firecrawl-js';
import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';

dotenv.config();

const fc = new Firecrawl({ apiKey: process.env.FIRECRAWL_API_KEY });
const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_KEY);

const SUBJECT = {
  name: 'Chemistry',
  code: '7405',
  qualification: 'A-Level',
  baseUrl: 'https://www.aqa.org.uk/subjects/chemistry/a-level/chemistry-7405/specification/subject-content'
};

// ================================================================
// STEP 1: CRAWL (Same as Biology)
// ================================================================

async function crawlChemistry() {
  console.log('🔍 Crawling Chemistry...');
  
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
      console.log(`   [${i + 1}] ${url.split('/').pop().substring(0, 40)}...`);
      
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
// STEP 2: PARSE (4 levels: numbered codes + table content)
// ================================================================

function parseChemistryTopics(pages) {
  console.log('\n📋 Parsing Chemistry topics...');
  
  const allTopics = [];
  
  for (const page of pages) {
    const markdown = page.markdown || '';
    const pageTopics = parseChemistryPage(markdown);
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

function parseChemistryPage(markdown) {
  const topics = [];
  const lines = markdown.split('\n');
  
  let currentLevel2Code = null;  // Track for table content
  let inTable = false;
  let rowCounter = 0;
  
  for (const line of lines) {
    // Numbered headings: ## 3.1, ### 3.1.1, #### 3.1.1.1
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
      
      // Track Level 2 codes (3.1.1.1) for table content
      if (level === 2) {
        currentLevel2Code = code;
        rowCounter = 0;
      }
      
      continue;
    }
    
    // Detect table start
    if (line.includes('Content') && line.includes('Opportunities')) {
      inTable = true;
      continue;
    }
    
    // Table separator
    if (line.match(/^\|?\s*[-:]+\s*\|/)) {
      continue;
    }
    
    // Parse table rows (Level 3)
    if (inTable && line.startsWith('|') && currentLevel2Code) {
      const cells = line.split('|').map(c => c.trim()).filter(c => c);
      
      if (cells.length >= 1 && cells[0].length > 10) {
        rowCounter++;
        const rowCode = `${currentLevel2Code}.${rowCounter}`;
        
        // Extract content (may have multiple lines/bullets)
        let content = cells[0]
          .replace(/<br\s*\/?>/gi, '\n')
          .replace(/<[^>]+>/g, '');
        
        // If content has bullets, split them
        const contentLines = content.split(/\n[•·-]\s*/).filter(l => l.trim().length > 5);
        
        contentLines.forEach((contentLine, idx) => {
          const bulletCode = `${rowCode}.${idx + 1}`;
          topics.push({
            code: bulletCode,
            title: contentLine.trim(),
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
  console.log('🚀 CHEMISTRY');
  console.log('='.repeat(60));
  
  try {
    const pages = await crawlChemistry();
    const topics = parseChemistryTopics(pages);
    await uploadToStaging(topics);
    
    console.log('\n' + '='.repeat(60));
    console.log('✅ CHEMISTRY COMPLETE!');
    console.log(`   Topics: ${topics.length}`);
    console.log('\nNext: python scrape-chemistry-papers.py');
    
  } catch (error) {
    console.error('\n❌ FAILED:', error.message);
    process.exit(1);
  }
}

main();

