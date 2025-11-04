/**
 * MASTER AQA GCSE TOPICS SCRAPER
 * Runs ALL GCSE subjects overnight
 * Uses patterns from A-Level scrapers
 */

import Firecrawl from '@mendable/firecrawl-js';
import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';
import fs from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

dotenv.config({ path: join(__dirname, '../../../.env') });

const fc = new Firecrawl({ apiKey: process.env.FIRECRAWL_API_KEY });
const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_KEY);

// Load subject list
const subjectsData = JSON.parse(fs.readFileSync(join(__dirname, 'aqa-gcse-subjects.json'), 'utf8'));
const subjects = subjectsData.subjects;

// Utility: Clean markdown formatting
function cleanMarkdown(text) {
  return text
    .replace(/\*\*(.+?)\*\*/g, '$1')
    .replace(/\*(.+?)\*/g, '$1')
    .replace(/_(.+?)_/g, '$1')
    .replace(/`(.+?)`/g, '$1')
    .trim();
}

// Pattern 1: Numbered hierarchy with bullets (most subjects)
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
      
      if (level <= maxDepth) {
        topics.push({ code, title, level, parentCode: level > 0 ? code.split('.').slice(0, -1).join('.') : null });
        currentCode = code;
      }
      continue;
    }
    
    const bulletMatch = line.match(/^-\s+[•·]?\s*(.{5,})/);
    if (bulletMatch && currentCode) {
      const currentLevel = currentCode.split('.').length - 2;
      if (currentLevel < maxDepth) {
        const bulletNum = topics.filter(t => t.parentCode === currentCode).length + 1;
        const bulletCode = `${currentCode}.${bulletNum}`;
        topics.push({ code: bulletCode, title: cleanMarkdown(bulletMatch[1].trim()), level: currentLevel + 1, parentCode: currentCode });
      }
    }
  }
  
  return topics;
}

// Pattern 2: Table-based (Business, Economics, etc.)
function parseTablesWithContent(markdown) {
  const topics = [];
  const lines = markdown.split('\n');
  let currentL0 = null;
  let currentL1 = null;
  let currentL2 = null;
  let inTable = false;
  let tableRowCounter = 1;
  
  for (const line of lines) {
    const numberedMatch = line.match(/^#{2,6}\s+(\d+(?:\.\d+)+)\s+(.+)$/);
    if (numberedMatch) {
      const code = numberedMatch[1];
      const title = cleanMarkdown(numberedMatch[2].trim());
      const level = code.split('.').length - 2;
      const parts = code.split('.');
      const parentCode = level > 0 ? parts.slice(0, -1).join('.') : null;
      
      topics.push({ code, title, level, parentCode });
      
      if (level === 0) { currentL0 = code; currentL1 = null; currentL2 = null; }
      else if (level === 1) { currentL1 = code; currentL2 = null; }
      else if (level === 2) { currentL2 = code; }
      
      inTable = false;
      tableRowCounter = 1;
      continue;
    }
    
    if (line.includes('|') && line.toLowerCase().includes('content')) {
      inTable = true;
      tableRowCounter = 1;
      continue;
    }
    
    if (line.match(/^\|[\s\-:]+\|/)) continue;
    
    if (inTable && line.startsWith('|')) {
      const columns = line.split('|').map(c => c.trim()).filter(c => c);
      if (columns.length >= 1 && columns[0] && columns[0].length > 5 && !columns[0].toLowerCase().includes('content')) {
        const parent = currentL2 || currentL1 || currentL0;
        const code = `${parent}.${tableRowCounter}`;
        topics.push({ code, title: cleanMarkdown(columns[0]), level: 3, parentCode: parent });
        tableRowCounter++;
      }
    }
    
    if (inTable && line.match(/^#{2,6}/)) inTable = false;
  }
  
  return topics;
}

// Scrape one subject
async function scrapeGCSESubject(subject) {
  console.log(`\n${'='.repeat(70)}`);
  console.log(`🔍 ${subject.name} (${subject.code})`);
  console.log('='.repeat(70));
  
  try {
    const baseUrl = `https://www.aqa.org.uk/subjects/${subject.slug}/gcse/${subject.slug}-${subject.code}/specification/subject-content`;
    
    // Map to find sub-pages
    const mapResult = await fc.mapUrl(baseUrl, { includeSubdomains: false, limit: 50 });
    const urls = mapResult.links || [];
    const contentUrls = urls.filter(u => u.includes('/specification/subject-content/') && !u.includes('/downloads/') && u !== baseUrl);
    
    console.log(`✅ Found ${contentUrls.length} content pages`);
    
    const pages = [];
    for (let i = 0; i < contentUrls.length; i++) {
      const slug = contentUrls[i].split('/').pop();
      console.log(`   [${i + 1}/${contentUrls.length}] ${slug}...`);
      try {
        const result = await fc.scrapeUrl(contentUrls[i], { formats: ['markdown'], onlyMainContent: true });
        pages.push({ ...result, url: contentUrls[i] });
      } catch (err) { 
        console.warn(`   ⚠️  Failed: ${err.message}`); 
      }
    }
    
    console.log(`✅ Scraped ${pages.length} pages`);
    
    // Parse based on pattern
    let allTopics = [];
    for (const page of pages) {
      const markdown = page.markdown || '';
      let pageTopics = [];
      
      if (subject.pattern === 'table') {
        pageTopics = parseTablesWithContent(markdown);
      } else {
        // Default: numbered with bullets (depth 2 for GCSE)
        pageTopics = parseNumberedWithBullets(markdown, 2);
      }
      
      allTopics.push(...pageTopics);
    }
    
    // Deduplicate
    const unique = [];
    const seen = new Set();
    for (const topic of allTopics) {
      if (!seen.has(topic.code) && topic.code) { 
        unique.push(topic); 
        seen.add(topic.code); 
      }
    }
    
    console.log(`📊 Total topics: ${unique.length}`);
    const levels = {};
    unique.forEach(t => levels[t.level] = (levels[t.level] || 0) + 1);
    Object.keys(levels).sort().forEach(l => console.log(`   Level ${l}: ${levels[l]}`));
    
    // Upload to database
    await uploadToStaging(subject, unique);
    
    return { success: true, topics: unique.length };
    
  } catch (error) {
    console.error(`❌ FAILED: ${error.message}`);
    return { success: false, error: error.message };
  }
}

async function uploadToStaging(subjectInfo, topics) {
  const { data: subject } = await supabase.from('staging_aqa_subjects').upsert({
    subject_name: `${subjectInfo.name} (GCSE)`,
    subject_code: subjectInfo.code,
    qualification_type: 'GCSE',
    specification_url: `https://www.aqa.org.uk/subjects/${subjectInfo.slug}/gcse/${subjectInfo.slug}-${subjectInfo.code}/specification/subject-content`
  }, { onConflict: 'subject_code,qualification_type' }).select().single();
  
  console.log(`💾 Subject ID: ${subject.id}`);
  
  await supabase.from('staging_aqa_topics').delete().eq('subject_id', subject.id);
  
  const toInsert = topics.map(t => ({ 
    subject_id: subject.id, 
    topic_code: t.code, 
    topic_name: t.title, 
    topic_level: t.level 
  }));
  
  const { data: inserted } = await supabase.from('staging_aqa_topics').insert(toInsert).select();
  console.log(`✅ Uploaded ${inserted.length} topics`);
  
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
}

// Main: Run all subjects
async function main() {
  console.log('🚀 AQA GCSE MASTER SCRAPER');
  console.log('='.repeat(70));
  console.log(`📚 Total subjects to scrape: ${subjects.length}`);
  console.log('='.repeat(70));
  
  const results = [];
  let successCount = 0;
  
  for (let i = 0; i < subjects.length; i++) {
    const subject = subjects[i];
    console.log(`\n[${i + 1}/${subjects.length}] Starting ${subject.name}...`);
    
    const result = await scrapeGCSESubject(subject);
    results.push({ subject: subject.name, ...result });
    
    if (result.success) {
      successCount++;
      console.log(`✅ ${subject.name} COMPLETE!`);
    } else {
      console.log(`❌ ${subject.name} FAILED: ${result.error}`);
    }
    
    // Small delay between subjects
    await new Promise(resolve => setTimeout(resolve, 2000));
  }
  
  console.log('\n' + '='.repeat(70));
  console.log('🎉 GCSE SCRAPING COMPLETE!');
  console.log('='.repeat(70));
  console.log(`✅ Success: ${successCount}/${subjects.length}`);
  console.log(`❌ Failed: ${subjects.length - successCount}`);
  console.log('\nResults:');
  results.forEach(r => {
    console.log(`  ${r.success ? '✅' : '❌'} ${r.subject}: ${r.topics || 0} topics`);
  });
}

main();

