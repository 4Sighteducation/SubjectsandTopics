/**
 * AQA MUSIC A-LEVEL Scraper
 * Code: 7272
 * Structure: Areas of Study + Set Works (like English Lit)
 * 3 main sections: Appraising, Performance, Composition
 */

import Firecrawl from '@mendable/firecrawl-js';
import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';

dotenv.config();

const fc = new Firecrawl({ apiKey: process.env.FIRECRAWL_API_KEY });
const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_KEY);

const SUBJECT = {
  name: 'Music',
  code: '7272',
  qualification: 'A-Level',
  baseUrl: 'https://www.aqa.org.uk/subjects/music/a-level/music-7272/specification/subject-content'
};

async function crawlMusic() {
  console.log('🔍 Crawling Music...');
  try {
    // Scrape the 3 main sub-pages
    const pages = [];
    const urls = [
      'https://www.aqa.org.uk/subjects/music/a-level/music-7272/specification/subject-content/appraising-music',
      'https://www.aqa.org.uk/subjects/music/a-level/music-7272/specification/subject-content/performance',
      'https://www.aqa.org.uk/subjects/music/a-level/music-7272/specification/subject-content/composition'
    ];
    
    for (let i = 0; i < urls.length; i++) {
      console.log(`   [${i + 1}] ${urls[i].split('/').pop()}...`);
      try {
        const result = await fc.scrapeUrl(urls[i], { formats: ['markdown'], onlyMainContent: true });
        pages.push({ ...result, url: urls[i], slug: urls[i].split('/').pop() });
      } catch (err) { console.warn(`   ⚠️  Failed`); }
    }
    console.log(`✅ Scraped ${pages.length} pages`);
    return pages;
  } catch (error) {
    console.error('❌ Crawl failed:', error.message);
    throw error;
  }
}

function parseMusicTopics(pages) {
  console.log('\n📋 Parsing Music topics...');
  const allTopics = [];
  
  for (const page of pages) {
    const markdown = page.markdown || '';
    const slug = page.slug || '';
    
    if (slug === 'appraising-music') {
      const topics = parseAppraisingMusic(markdown);
      allTopics.push(...topics);
    } else if (slug === 'performance') {
      allTopics.push({ code: '3.2', title: 'Performance', level: 0, parentCode: null });
    } else if (slug === 'composition') {
      allTopics.push({ code: '3.3', title: 'Composition', level: 0, parentCode: null });
    }
  }
  
  console.log(`✅ Total: ${allTopics.length}`);
  const levels = {};
  allTopics.forEach(t => levels[t.level] = (levels[t.level] || 0) + 1);
  Object.keys(levels).sort().forEach(l => console.log(`   Level ${l}: ${levels[l]}`));
  
  return allTopics;
}

function cleanMarkdown(text) {
  return text
    .replace(/\*\*(.+?)\*\*/g, '$1')
    .replace(/\*(.+?)\*/g, '$1')
    .replace(/_(.+?)_/g, '$1')
    .replace(/`(.+?)`/g, '$1')
    .trim();
}

function parseAppraisingMusic(markdown) {
  const topics = [];
  const lines = markdown.split('\n');
  let areaNumber = 1;
  let strandLetter = 'A';
  
  // Add main Appraising section
  topics.push({ code: '3.1', title: 'Appraising music', level: 0, parentCode: null });
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    
    // Area of study headings (e.g., "Area of study 1:", "Area of study 2:")
    const areaMatch = line.match(/^#{2,3}\s+Area of study (\d+):\s+(.+)$/i);
    if (areaMatch) {
      const num = areaMatch[1];
      const title = cleanMarkdown(areaMatch[2].trim());
      const code = `3.1.${num}`;
      topics.push({ code, title: `Area ${num}: ${title}`, level: 1, parentCode: '3.1' });
      continue;
    }
    
    // Strand headings (e.g., "Strand A: Baroque solo concerto")
    const strandMatch = line.match(/^#{3,4}\s+(?:Strand\s+)?([A-Z]):\s+(.+)$/i);
    if (strandMatch) {
      const letter = strandMatch[1];
      const title = cleanMarkdown(strandMatch[2].trim());
      const code = `3.1.1.${letter}`;
      topics.push({ code, title: `Strand ${letter}: ${title}`, level: 2, parentCode: '3.1.1' });
      strandLetter = letter;
      continue;
    }
    
    // Table rows with Composer | Set works
    if (line.startsWith('|') && !line.match(/^\|[\s\-:]+\|/)) {
      const cells = line.split('|').map(c => c.trim()).filter(c => c);
      
      // Skip header rows
      if (cells.length >= 2 && cells[0] && cells[1] && 
          !cells[0].toLowerCase().includes('composer') &&
          !cells[0].toLowerCase().includes('element')) {
        
        const composer = cleanMarkdown(cells[0]);
        const works = cleanMarkdown(cells[1]);
        
        // Skip empty rows
        if (composer.length < 2 || works.length < 2) continue;
        
        // Create topic: "Composer - Work"
        const workCounter = topics.filter(t => t.parentCode === `3.1.1.${strandLetter}`).length + 1;
        const code = `3.1.1.${strandLetter}.${workCounter}`;
        
        topics.push({
          code,
          title: `${composer} - ${works}`,
          level: 3,
          parentCode: `3.1.1.${strandLetter}`
        });
      }
    }
  }
  
  return topics;
}

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
    
    const toInsert = topics.map(t => ({ subject_id: subject.id, topic_code: t.code, topic_name: t.title, topic_level: t.level }));
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
  } catch (error) {
    console.error('❌ Upload failed:', error);
    throw error;
  }
}

async function main() {
  console.log('🚀 MUSIC');
  console.log('='.repeat(60));
  try {
    const pages = await crawlMusic();
    const topics = parseMusicTopics(pages);
    await uploadToStaging(topics);
    console.log('\n✅ MUSIC COMPLETE! Topics:', topics.length);
  } catch (error) {
    console.error('\n❌ FAILED:', error.message);
    process.exit(1);
  }
}

main();
