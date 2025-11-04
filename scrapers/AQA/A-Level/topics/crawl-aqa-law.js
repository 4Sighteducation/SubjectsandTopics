/**
 * AQA LAW A-LEVEL Scraper
 * Code: 7162
 * Table-based structure with Content | Additional Information
 * Topics need auto-numbering based on table row order
 * 5 sections: Nature of law, Criminal law, Tort, Contract, Human Rights
 */

import Firecrawl from '@mendable/firecrawl-js';
import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';

dotenv.config();

const fc = new Firecrawl({ apiKey: process.env.FIRECRAWL_API_KEY });
const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_KEY);

const SUBJECT = {
  name: 'Law',
  code: '7162',
  qualification: 'A-Level',
  baseUrl: 'https://www.aqa.org.uk/subjects/law/a-level/law-7162/specification/subject-content'
};

// Standard crawl
async function crawlLaw() {
  console.log('🔍 Crawling Law...');
  try {
    const mapResult = await fc.mapUrl(SUBJECT.baseUrl, { includeSubdomains: false, limit: 50 });
    const urls = mapResult.links || [];
    const contentUrls = urls.filter(u => u.includes('/specification/subject-content/') && !u.includes('/downloads/') && u !== SUBJECT.baseUrl);
    
    console.log(`✅ Found ${contentUrls.length} pages`);
    const pages = [];
    for (let i = 0; i < contentUrls.length; i++) {
      console.log(`   [${i + 1}] ${contentUrls[i].split('/').pop()}...`);
      try {
        const result = await fc.scrapeUrl(contentUrls[i], { formats: ['markdown'], onlyMainContent: true });
        pages.push({ ...result, url: contentUrls[i] });
      } catch (err) { console.warn(`   ⚠️  Failed`); }
    }
    console.log(`✅ Scraped ${pages.length} pages`);
    return pages;
  } catch (error) {
    console.error('❌ Crawl failed:', error.message);
    throw error;
  }
}

// Parse tables with auto-numbering
function parseLawTopics(pages) {
  console.log('\n📋 Parsing Law topics...');
  const allTopics = [];
  
  for (const page of pages) {
    const markdown = page.markdown || '';
    const pageTopics = parseTablesAndHeadings(markdown);
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

// Clean markdown formatting
function cleanMarkdown(text) {
  return text
    .replace(/\*\*(.+?)\*\*/g, '$1')
    .replace(/\*(.+?)\*/g, '$1')
    .replace(/_(.+?)_/g, '$1')
    .replace(/`(.+?)`/g, '$1')
    .trim();
}

function parseTablesAndHeadings(markdown) {
  const topics = [];
  const lines = markdown.split('\n');
  let currentSection = null;
  let topicCounter = 1;
  let inTable = false;
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    
    // Detect main section headings (## 3.1, ## 3.2, etc.)
    const sectionMatch = line.match(/^#{2}\s+(\d+\.\d+)\s+(.+)$/);
    if (sectionMatch) {
      const sectionCode = sectionMatch[1];
      const sectionTitle = cleanMarkdown(sectionMatch[2].trim());
      currentSection = sectionCode;
      topicCounter = 1;
      
      topics.push({
        code: sectionCode,
        title: sectionTitle,
        level: 0,
        parentCode: null
      });
      
      inTable = false;
      continue;
    }
    
    // Detect table header
    if (line.includes('|') && (line.toLowerCase().includes('content') || line.toLowerCase().includes('additional information'))) {
      inTable = true;
      continue;
    }
    
    // Skip table separator line
    if (line.match(/^\|[\s\-:]+\|/)) {
      continue;
    }
    
    // Parse table rows - BOTH columns
    if (inTable && line.includes('|') && currentSection) {
      const columns = line.split('|').map(c => c.trim()).filter(c => c);
      
      if (columns.length >= 1 && columns[0]) {
        const contentCell = columns[0];
        const additionalCell = columns.length >= 2 ? columns[1] : '';
        const cleanContent = cleanMarkdown(contentCell);
        
        // Skip empty rows or header-like content
        if (!cleanContent || cleanContent.length < 3) continue;
        
        // Create auto-numbered code for main content (Level 1)
        const topicCode = `${currentSection}.${topicCounter}`;
        
        topics.push({
          code: topicCode,
          title: cleanContent,
          level: 1,
          parentCode: currentSection
        });
        
        // Parse bullets from Additional Information column (Level 2)
        if (additionalCell) {
          const bulletLines = additionalCell.split('\n');
          let bulletCounter = 1;
          
          for (const bulletLine of bulletLines) {
            const bulletMatch = bulletLine.match(/^[•\-\*]\s+(.{5,})/);
            if (bulletMatch) {
              const bulletText = cleanMarkdown(bulletMatch[1].trim());
              const bulletCode = `${topicCode}.${bulletCounter}`;
              
              topics.push({
                code: bulletCode,
                title: bulletText,
                level: 2,
                parentCode: topicCode
              });
              
              bulletCounter++;
            }
          }
        }
        
        topicCounter++;
      }
    }
    
    // Stop table parsing if we hit a non-table line
    if (inTable && !line.includes('|') && line.trim()) {
      inTable = false;
    }
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
  console.log('🚀 LAW');
  console.log('='.repeat(60));
  try {
    const pages = await crawlLaw();
    const topics = parseLawTopics(pages);
    await uploadToStaging(topics);
    console.log('\n✅ LAW COMPLETE! Topics:', topics.length);
  } catch (error) {
    console.error('\n❌ FAILED:', error.message);
    process.exit(1);
  }
}

main();

