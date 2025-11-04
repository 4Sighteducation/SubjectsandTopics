/**
 * AQA HEBREW (BIBLICAL) A-LEVEL Scraper
 * Code: 7677
 * Special handling: 3.1 & 3.2 are L0 only, 3.3-3.5 need deeper scraping
 * Contains Hebrew text (right-to-left Unicode)
 */

import Firecrawl from '@mendable/firecrawl-js';
import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';

dotenv.config();

const fc = new Firecrawl({ apiKey: process.env.FIRECRAWL_API_KEY });
const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_KEY);

const SUBJECT = {
  name: 'Hebrew (Biblical)',
  code: '7677',
  qualification: 'A-Level',
  baseUrl: 'https://www.aqa.org.uk/subjects/hebrew-(biblical)/a-level/hebrew-(biblical)-7677/specification/subject-content'
};

// Crawl with all pages
async function crawlHebrew() {
  console.log('🔍 Crawling Hebrew (Biblical)...');
  try {
    const mapResult = await fc.mapUrl(SUBJECT.baseUrl, { includeSubdomains: false, limit: 50 });
    const urls = mapResult.links || [];
    console.log(`🔍 Map found ${urls.length} total URLs`);
    if (urls.length > 0 && urls.length < 20) {
      console.log('   URLs found:', urls.slice(0, 10));
    }
    
    const contentUrls = urls.filter(u => u.includes('/specification/subject-content/') && !u.includes('/downloads/') && u !== SUBJECT.baseUrl);
    
    console.log(`✅ Found ${contentUrls.length} matching pages`);
    const pages = [];
    for (let i = 0; i < contentUrls.length; i++) {
      const url = contentUrls[i];
      const slug = url.split('/').pop();
      console.log(`   [${i + 1}] ${slug}...`);
      try {
        const result = await fc.scrapeUrl(url, { formats: ['markdown'], onlyMainContent: true });
        pages.push({ ...result, url, slug });
      } catch (err) { 
        console.warn(`   ⚠️  Failed: ${err.message}`); 
      }
    }
    console.log(`✅ Scraped ${pages.length} pages`);
    return pages;
  } catch (error) {
    console.error('❌ Crawl failed:', error.message);
    throw error;
  }
}

// Parse with selective depth control
function parseHebrewTopics(pages) {
  console.log('\n📋 Parsing Hebrew (Biblical) topics...');
  const allTopics = [];
  
  for (const page of pages) {
    const markdown = page.markdown || '';
    const slug = page.slug || '';
    
    // Determine depth based on section
    let maxDepth = 3; // Default: parse deep
    
    // L0 only for 3.1 and 3.2
    if (slug.includes('unseen-translation') || slug.includes('prose-literature')) {
      maxDepth = 0;
      console.log(`   ${slug}: Level 0 only`);
    } else {
      console.log(`   ${slug}: Up to Level ${maxDepth}`);
    }
    
    const pageTopics = parseNumberedWithBullets(markdown, maxDepth);
    allTopics.push(...pageTopics);
  }
  
  // Deduplicate by code
  const unique = [];
  const seen = new Set();
  for (const topic of allTopics) {
    if (!seen.has(topic.code) && topic.code) { 
      unique.push(topic); 
      seen.add(topic.code); 
    }
  }
  
  console.log(`✅ Total: ${unique.length}`);
  const levels = {};
  unique.forEach(t => levels[t.level] = (levels[t.level] || 0) + 1);
  Object.keys(levels).sort().forEach(l => console.log(`   Level ${l}: ${levels[l]}`));
  
  return unique;
}

// Clean markdown formatting from text (italics, bold, etc.)
function cleanMarkdown(text) {
  return text
    .replace(/\*\*(.+?)\*\*/g, '$1')  // Remove bold **text**
    .replace(/\*(.+?)\*/g, '$1')      // Remove italics *text*
    .replace(/_(.+?)_/g, '$1')        // Remove italics _text_
    .replace(/`(.+?)`/g, '$1')        // Remove code `text`
    .trim();
}

function parseNumberedWithBullets(markdown, maxDepth = 3) {
  const topics = [];
  const lines = markdown.split('\n');
  let currentCode = null;
  
  for (const line of lines) {
    const numberedMatch = line.match(/^#{2,6}\s+(\d+(?:\.\d+)+)\s+(.+)$/);
    if (numberedMatch) {
      const code = numberedMatch[1];
      const title = cleanMarkdown(numberedMatch[2].trim());
      const level = code.split('.').length - 2;
      
      // Skip if beyond maxDepth
      if (level > maxDepth) continue;
      
      topics.push({ code, title, level, parentCode: level > 0 ? code.split('.').slice(0, -1).join('.') : null });
      currentCode = code;
      continue;
    }
    
    // REMOVED: Don't auto-number bullets as topics
    // This was creating conflicts with real numbered headings
    // For example, bullets under 3.5 were becoming 3.5.1, 3.5.2
    // which conflicted with the real "### 3.5.1 General vocabulary" heading
  }
  
  return topics;
}

// Standard upload
async function uploadToStaging(topics) {
  console.log('\n💾 Uploading...');
  try {
    const { data: subject } = await supabase.from('staging_aqa_subjects').upsert({
      subject_name: `${SUBJECT.name} (${SUBJECT.qualification})`, 
      subject_code: SUBJECT.code,
      qualification_type: SUBJECT.qualification, 
      specification_url: SUBJECT.baseUrl
    }, { onConflict: 'subject_code,qualification_type' }).select().single();
    
    console.log(`✅ Subject: ${subject.subject_name}`);
    await supabase.from('staging_aqa_topics').delete().eq('subject_id', subject.id);
    
    const toInsert = topics.map(t => ({ 
      subject_id: subject.id, 
      topic_code: t.code, 
      topic_name: t.title, 
      topic_level: t.level 
    }));
    
    const { data: inserted } = await supabase.from('staging_aqa_topics').insert(toInsert).select();
    console.log(`✅ Uploaded ${inserted.length} topics`);
    
    // Link parent-child relationships
    const codeToId = new Map(inserted.map(t => [t.topic_code, t.id]));
    let linked = 0;
    for (const topic of topics) {
      if (topic.parentCode) {
        const parentId = codeToId.get(topic.parentCode);
        const childId = codeToId.get(topic.code);
        if (parentId && childId) {
          await supabase.from('staging_aqa_topics').update({ parent_topic_id: parentId }).eq('id', childId);
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

async function main() {
  console.log('🚀 HEBREW (BIBLICAL)');
  console.log('='.repeat(60));
  try {
    const pages = await crawlHebrew();
    const topics = parseHebrewTopics(pages);
    await uploadToStaging(topics);
    console.log('\n✅ HEBREW (BIBLICAL) COMPLETE! Topics:', topics.length);
  } catch (error) {
    console.error('\n❌ FAILED:', error.message);
    process.exit(1);
  }
}

main();

