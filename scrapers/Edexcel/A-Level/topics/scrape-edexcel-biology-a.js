/**
 * Edexcel Biology A (Salters-Nuffield) A-Level Topic Scraper
 * Code: 9BN0
 * 
 * Much simpler than History - just 3 Papers and 8 Topics!
 * Extracts full content, then AI cleanup script can summarize later.
 */

import Firecrawl from '@mendable/firecrawl-js';
import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';
import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';

// Get directory and load .env
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
dotenv.config({ path: path.join(__dirname, '../../../../.env') });

const fc = new Firecrawl({ apiKey: process.env.FIRECRAWL_API_KEY });
const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_KEY);

// ================================================================
// CONFIG: Edexcel Biology A
// ================================================================

const SUBJECT = {
  name: 'Biology A (Salters-Nuffield)',
  code: '9BN0',
  qualification: 'A-Level',
  exam_board: 'Edexcel',
  // Try simpler URL without encoded characters
  specificationPDF: 'https://qualifications.pearson.com/content/dam/pdf/A-Level/biology-a/2015/specification-and-sample-assessment-materials/9781446930885-gce2015-a-bioa-spec.pdf'
};

// ================================================================
// STEP 1: SCRAPE PDF
// ================================================================

async function scrapePDF() {
  console.log('📄 Scraping Biology A specification PDF...');
  console.log(`   URL: ${SUBJECT.specificationPDF}`);
  console.log('   This may take 60-90 seconds...\n');
  
  const maxRetries = 2;
  let attempt = 0;
  
  while (attempt <= maxRetries) {
    try {
      if (attempt > 0) {
        console.log(`   Retry attempt ${attempt}/${maxRetries}...`);
      }
      
      const result = await fc.scrapeUrl(SUBJECT.specificationPDF, {
        formats: ['markdown'],
        onlyMainContent: true
        // No timeout - let Firecrawl use its default
      });
      
      const markdown = result.markdown || '';
      
      console.log(`✅ PDF scraped successfully!`);
      console.log(`   Content length: ${markdown.length} characters`);
      
      // Save for debugging
      const debugPath = path.join(__dirname, '../../../../debug-edexcel-biology-a-spec.md');
      await fs.writeFile(debugPath, markdown);
      console.log(`   Saved to debug-edexcel-biology-a-spec.md`);
      
      return markdown;
      
    } catch (error) {
      attempt++;
      if (attempt > maxRetries) {
        console.error('❌ PDF scraping failed:', error.message);
        throw error;
      }
      console.warn(`   ⚠️  Attempt failed, retrying...`);
      await new Promise(resolve => setTimeout(resolve, 5000));
    }
  }
}

// ================================================================
// STEP 2: PARSE BIOLOGY TOPICS
// ================================================================

function parseBiologyTopics(markdown) {
  console.log('\n📋 Parsing Biology topics...');
  
  const topics = [];
  const lines = markdown.split('\n');
  
  // Biology structure (simple!):
  // Level 0: Paper 1, Paper 2, Paper 3
  // Level 1: Topic 1, Topic 2, ..., Topic 8
  // Level 2: 1.1, 1.2, 1.3, 1.4, etc. (numbered items)
  // Level 3: 1.4.i, 1.4.ii (sub-items with i, ii, iii)
  
  let currentPaper = null;
  let currentTopic = null;
  let currentItem = null;
  
  // Create Papers (3 papers)
  topics.push({ code: 'Paper1', title: 'Paper 1: The Natural Environment and Species Survival', level: 0, parentCode: null });
  topics.push({ code: 'Paper2', title: 'Paper 2: Energy, Exercise and Co-ordination', level: 0, parentCode: null });
  topics.push({ code: 'Paper3', title: 'Paper 3: General and Practical Applications in Biology', level: 0, parentCode: null });
  
  // Map topics to papers based on PDF content
  const topicToPaper = {
    'Topic1': 'Paper1', 'Topic2': 'Paper1', 'Topic3': 'Paper1', 
    'Topic4': 'Paper1', 'Topic5': 'Paper1', 'Topic6': 'Paper1',
    'Topic7': 'Paper2', 'Topic8': 'Paper2'
    // Paper 3 covers all topics (synoptic)
  };
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line) continue;
    
    // Skip core practicals and appendices
    if (line.match(/CORE PRACTICAL|Appendix|Assessment Objectives/i)) {
      continue;
    }
    
    // Pattern 1: Topic headings "Topic 1: Lifestyle, Health and Risk"
    const topicMatch = line.match(/^Topic\s+(\d+):\s+(.+)$/i);
    if (topicMatch) {
      const topicNum = topicMatch[1];
      const topicTitle = topicMatch[2].trim();
      const code = `Topic${topicNum}`;
      
      currentTopic = code;
      currentItem = null;
      
      // Determine parent paper
      const parentPaper = topicToPaper[code] || 'Paper1';
      
      topics.push({
        code,
        title: `Topic ${topicNum}: ${topicTitle}`,
        level: 1,
        parentCode: parentPaper
      });
      
      console.log(`   Found ${code}`);
      continue;
    }
    
    if (!currentTopic) continue;
    
    // Pattern 2: Main numbered items "1.1 Understand why..."
    const itemMatch = line.match(/^(\d+)\.(\d+)\s+(.+)$/);
    if (itemMatch) {
      const major = itemMatch[1];
      const minor = itemMatch[2];
      const content = itemMatch[3].trim();
      const code = `${major}.${minor}`;
      
      currentItem = code;
      
      topics.push({
        code,
        title: content,  // Full content for now - AI will clean later
        level: 2,
        parentCode: currentTopic
      });
      
      continue;
    }
    
    // Pattern 3: Sub-items with i), ii), iii)
    const subItemMatch = line.match(/^([ivx]+)\)\s+(.+)$/i);
    if (subItemMatch && currentItem) {
      const roman = subItemMatch[1].toLowerCase();
      const content = subItemMatch[2].trim();
      
      // Convert roman to number
      const romanMap = { 'i': 1, 'ii': 2, 'iii': 3, 'iv': 4, 'v': 5 };
      const subNum = romanMap[roman] || 1;
      
      const code = `${currentItem}.${subNum}`;
      
      topics.push({
        code,
        title: content,  // Full content for now
        level: 3,
        parentCode: currentItem
      });
    }
  }
  
  // Remove duplicates
  const unique = [];
  const seen = new Set();
  
  for (const topic of topics) {
    if (!seen.has(topic.code)) {
      unique.push(topic);
      seen.add(topic.code);
    }
  }
  
  console.log(`✅ Parsed ${unique.length} unique topics`);
  
  // Distribution
  const levels = {};
  unique.forEach(t => levels[t.level] = (levels[t.level] || 0) + 1);
  
  console.log('   Distribution:');
  Object.keys(levels).sort().forEach(l => {
    console.log(`   Level ${l}: ${levels[l]} topics`);
  });
  
  // Sample
  console.log('\n   Sample structure:');
  const topic1 = unique.find(t => t.code === 'Topic1');
  if (topic1) {
    console.log(`   ${topic1.title}`);
    const items = unique.filter(t => t.parentCode === 'Topic1').slice(0, 3);
    items.forEach(item => {
      console.log(`   ├─ ${item.code} - ${item.title.substring(0, 60)}...`);
      const subs = unique.filter(t => t.parentCode === item.code);
      subs.forEach(sub => {
        console.log(`   │  └─ ${sub.code} - ${sub.title.substring(0, 50)}...`);
      });
    });
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
        specification_url: SUBJECT.specificationPDF,
        exam_board: SUBJECT.exam_board
      }, { onConflict: 'subject_code,qualification_type,exam_board' })
      .select()
      .single();
    
    if (subjectError) throw subjectError;
    console.log(`✅ Subject: ${subject.subject_name} [${SUBJECT.exam_board}]`);
    
    // 2. DELETE old topics
    await supabase
      .from('staging_aqa_topics')
      .delete()
      .eq('subject_id', subject.id);
    
    console.log(`✅ Cleared old topics`);
    
    // 3. Insert topics
    const topicsToInsert = topics.map(t => ({
      subject_id: subject.id,
      topic_code: t.code,
      topic_name: t.title,
      topic_level: t.level,
      exam_board: SUBJECT.exam_board
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
// MAIN
// ================================================================

async function main() {
  console.log('🚀 EDEXCEL BIOLOGY A - TOPIC SCRAPER');
  console.log('='.repeat(60));
  console.log(`\nSubject: ${SUBJECT.name}`);
  console.log(`Code: ${SUBJECT.code}`);
  console.log(`Exam Board: ${SUBJECT.exam_board}`);
  console.log(`\nExpected hierarchy:`);
  console.log(`  Level 0: Papers (1, 2, 3)`);
  console.log(`  Level 1: Topics (1-8)`);
  console.log(`  Level 2: Items (1.1, 1.2, etc.)`);
  console.log(`  Level 3: Sub-items (1.4.i, 1.4.ii)`);
  console.log('');
  
  try {
    // Step 1: Scrape PDF
    const markdown = await scrapePDF();
    
    // Step 2: Parse topics
    const topics = parseBiologyTopics(markdown);
    
    // Step 3: Upload
    const subjectId = await uploadToStaging(topics);
    
    console.log('\n' + '='.repeat(60));
    console.log('✅ BIOLOGY A - TOPICS COMPLETE!');
    console.log(`   Total topics: ${topics.length}`);
    console.log(`   Exam board: ${SUBJECT.exam_board}`);
    console.log('\n💡 Next steps:');
    console.log('   1. Check topics in Supabase');
    console.log('   2. Run AI cleanup script (coming next!)');
    console.log('   3. Run papers scraper');
    
  } catch (error) {
    console.error('\n❌ FAILED:', error.message);
    console.error(error.stack);
    process.exit(1);
  }
}

main();

