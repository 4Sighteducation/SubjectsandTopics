/**
 * DAY 1 TEST: Firecrawl + AQA Biology
 * 
 * Purpose: Prove the concept with ONE subject before scaling
 * Success: Clean topic data in staging_aqa tables
 * Time: ~2 hours
 */

import Firecrawl from '@mendable/firecrawl-js';
import { createClient } from '@supabase/supabase-js';
import crypto from 'crypto';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

// ================================================================
// CONFIGURATION
// ================================================================

const FIRECRAWL_API_KEY = process.env.FIRECRAWL_API_KEY;
const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_SERVICE_KEY = process.env.SUPABASE_SERVICE_KEY;

if (!FIRECRAWL_API_KEY || !SUPABASE_URL || !SUPABASE_SERVICE_KEY) {
  console.error('❌ Missing environment variables!');
  console.log('Please set:');
  console.log('  - FIRECRAWL_API_KEY');
  console.log('  - SUPABASE_URL');
  console.log('  - SUPABASE_SERVICE_KEY');
  process.exit(1);
}

const fc = new Firecrawl({ apiKey: FIRECRAWL_API_KEY });
const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY);

// ================================================================
// TEST SUBJECT: AQA Biology A-Level (7402)
// ================================================================

const TEST_SUBJECT = {
  name: 'Biology',
  code: '7402',
  qualification: 'A-Level',
  url: 'https://www.aqa.org.uk/subjects/biology/a-level/biology-7402/specification/subject-content'
};

// ================================================================
// STEP 1: SCRAPE
// ================================================================

async function scrapeAQABiology() {
  console.log('🔍 Step 1: Scraping AQA Biology...');
  console.log(`   URL: ${TEST_SUBJECT.url}`);
  
  try {
    // Scrape the subject content page
    const result = await fc.scrapeUrl(TEST_SUBJECT.url, {
      formats: ['markdown', 'html'],
      onlyMainContent: true
    });
    
    console.log('✅ Scrape successful!');
    console.log(`   Markdown length: ${result.markdown?.length || 0} chars`);
    
    // Save for debugging
    await import('fs/promises').then(fs => 
      fs.writeFile('debug-scraped-content.md', result.markdown || '')
    );
    console.log('   💾 Saved to debug-scraped-content.md');
    
    return result;
  } catch (error) {
    console.error('❌ Scrape failed:', error.message);
    throw error;
  }
}

// ================================================================
// STEP 2: PARSE
// ================================================================

function parseTopics(markdown) {
  console.log('\n📋 Step 2: Parsing topics...');
  
  const topics = [];
  const lines = markdown.split('\n');
  
  // AQA uses BULLET LISTS with links, not headings!
  // Pattern: - • [3.1 Biological molecules](url)
  const bulletPattern = /^-\s*[•·]\s*\[(\d+(?:\.\d+)*)\s+([^\]]+)\]/;
  
  // Also try heading pattern as fallback
  const headingPattern = /^#{2,4}\s+(\d+(?:\.\d+)*)\s+(.+)$/;
  
  for (const line of lines) {
    // Try bullet pattern first
    let match = line.match(bulletPattern);
    let patternType = 'bullet';
    
    if (!match) {
      // Fallback to heading pattern
      match = line.match(headingPattern);
      patternType = 'heading';
    }
    
    if (match) {
      const [_, code, title] = match;
      const level = code.split('.').length - 1; // 3.1 = level 0, 3.1.1 = level 1
      
      // Check for "(A-level only)" flag
      const isALevelOnly = title.toLowerCase().includes('(a-level only)');
      const cleanTitle = title.replace(/\(A-level only\)/gi, '').trim();
      
      topics.push({
        code,
        title: cleanTitle,
        level,
        isALevelOnly,
        patternType,
        rawLine: line
      });
    }
  }
  
  console.log(`✅ Found ${topics.length} topics`);
  console.log('   Sample topics:');
  topics.slice(0, 8).forEach(t => {
    console.log(`   - ${t.code} ${t.title} (level ${t.level})`);
  });
  
  return topics;
}

// ================================================================
// STEP 3: BUILD HIERARCHY
// ================================================================

function buildHierarchy(topics) {
  console.log('\n🌳 Step 3: Building hierarchy...');
  
  // Map to track topic IDs by code
  const topicMap = new Map();
  
  // Build hierarchy by assigning parent codes
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
  
  // Validate hierarchy
  const topLevelCount = hierarchicalTopics.filter(t => !t.parentCode).length;
  console.log(`✅ Hierarchy built`);
  console.log(`   Top-level topics: ${topLevelCount}`);
  console.log(`   Expected for Biology: 7 (sections 3.1 through 3.7)`);
  
  if (topLevelCount !== 7) {
    console.warn('⚠️  Warning: Expected 7 top-level topics, found', topLevelCount);
  }
  
  return hierarchicalTopics;
}

// ================================================================
// STEP 4: UPLOAD TO STAGING
// ================================================================

async function uploadToStaging(topics, scrapeResult) {
  console.log('\n💾 Step 4: Uploading to staging database...');
  
  try {
    // 1. Insert or update subject
    console.log('   Inserting subject into staging_aqa_subjects...');
    const { data: subject, error: subjectError } = await supabase
      .from('staging_aqa_subjects')
      .upsert({
        subject_name: `${TEST_SUBJECT.name} (${TEST_SUBJECT.qualification})`,
        subject_code: TEST_SUBJECT.code,
        qualification_type: TEST_SUBJECT.qualification,
        specification_url: TEST_SUBJECT.url,
        spec_pdf_sha256: crypto
          .createHash('sha256')
          .update(scrapeResult.markdown || '')
          .digest('hex')
      }, {
        onConflict: 'subject_code,qualification_type'
      })
      .select()
      .single();
    
    if (subjectError) {
      console.error('   ❌ Subject insert failed:', subjectError);
      throw subjectError;
    }
    console.log(`✅ Subject uploaded: ${subject.subject_name}`);
    
    // 2. Delete existing topics for this subject (clean slate)
    const { error: deleteError } = await supabase
      .from('staging_aqa_topics')
      .delete()
      .eq('subject_id', subject.id);
    
    if (deleteError) throw deleteError;
    
    // 3. Insert topics
    const topicsToInsert = topics.map(topic => ({
      subject_id: subject.id,
      topic_code: topic.code,
      topic_name: topic.title,
      topic_level: topic.level,
      is_a_level_only: topic.isALevelOnly,
      parent_topic_id: null // Will link in second pass
    }));
    
    const { data: insertedTopics, error: topicsError } = await supabase
      .from('staging_aqa_topics')
      .insert(topicsToInsert)
      .select();
    
    if (topicsError) throw topicsError;
    
    console.log(`✅ ${insertedTopics.length} topics uploaded`);
    
    // 4. Link parent-child relationships (second pass)
    console.log('🔗 Linking parent-child relationships...');
    
    // Build code → ID map
    const codeToId = new Map(
      insertedTopics.map(t => [t.topic_code, t.id])
    );
    
    // Update parent_topic_id
    for (const topic of topics) {
      if (topic.parentCode) {
        const parentId = codeToId.get(topic.parentCode);
        const childId = codeToId.get(topic.code);
        
        if (parentId && childId) {
          const { error: updateError } = await supabase
            .from('staging_aqa_topics')
            .update({ parent_topic_id: parentId })
            .eq('id', childId);
          
          if (updateError) {
            console.warn(`⚠️  Failed to link ${topic.code} to parent:`, updateError.message);
          }
        }
      }
    }
    
    console.log('✅ Parent-child relationships linked');
    
    return subject;
  } catch (error) {
    console.error('❌ Upload failed:', error.message);
    throw error;
  }
}

// ================================================================
// STEP 5: VALIDATION
// ================================================================

async function validateData(subjectId) {
  console.log('\n✅ Step 5: Validating uploaded data...');
  
  try {
    // Count total topics
    const { count: totalTopics, error: countError } = await supabase
      .from('staging_aqa_topics')
      .select('*', { count: 'exact', head: true })
      .eq('subject_id', subjectId);
    
    if (countError) throw countError;
    
    // Count by level
    const { data: levelCounts, error: levelError } = await supabase
      .from('staging_aqa_topics')
      .select('topic_level')
      .eq('subject_id', subjectId);
    
    if (levelError) throw levelError;
    
    const levels = {};
    levelCounts.forEach(row => {
      levels[row.topic_level] = (levels[row.topic_level] || 0) + 1;
    });
    
    console.log('📊 Validation Results:');
    console.log(`   Total topics: ${totalTopics}`);
    console.log(`   Level 0 (main sections): ${levels[0] || 0} (expected: 7)`);
    console.log(`   Level 1 (subsections): ${levels[1] || 0}`);
    console.log(`   Level 2 (details): ${levels[2] || 0}`);
    
    // Check for duplicates
    const { data: duplicates, error: dupError } = await supabase
      .rpc('check_duplicates', { 
        schema_name: 'staging_aqa',
        table_name: 'topics',
        subject_uuid: subjectId
      })
      .select();
    
    // Simple duplicate check instead
    const { data: allTopics } = await supabase
      .from('staging_aqa_topics')
      .select('topic_name, topic_code')
      .eq('subject_id', subjectId);
    
    const seen = new Set();
    const dupes = [];
    allTopics?.forEach(t => {
      const key = `${t.topic_code}:${t.topic_name}`;
      if (seen.has(key)) dupes.push(key);
      seen.add(key);
    });
    
    if (dupes.length > 0) {
      console.log(`   ⚠️  Duplicates found: ${dupes.length}`);
      dupes.slice(0, 5).forEach(d => console.log(`      - ${d}`));
    } else {
      console.log('   ✅ No duplicates');
    }
    
    // Check parent-child links
    const { count: orphans } = await supabase
      .from('staging_aqa_topics')
      .select('*', { count: 'exact', head: true })
      .eq('subject_id', subjectId)
      .gt('topic_level', 0)
      .is('parent_topic_id', null);
    
    if (orphans > 0) {
      console.log(`   ⚠️  Orphaned topics (missing parent): ${orphans}`);
    } else {
      console.log('   ✅ All child topics have parents');
    }
    
    // Sample topics
    const { data: sampleTopics } = await supabase
      .from('staging_aqa_topics')
      .select('topic_code, topic_name, topic_level')
      .eq('subject_id', subjectId)
      .order('topic_code')
      .limit(10);
    
    console.log('\n📋 Sample topics:');
    sampleTopics?.forEach(t => {
      console.log(`   ${t.topic_code} - ${t.topic_name} (level ${t.topic_level})`);
    });
    
  } catch (error) {
    console.error('❌ Validation failed:', error.message);
  }
}

// ================================================================
// MAIN EXECUTION
// ================================================================

async function main() {
  console.log('🚀 AQA Biology Test Scrape');
  console.log('='.repeat(50));
  
  try {
    // Step 1: Scrape
    const scrapeResult = await scrapeAQABiology();
    
    // Step 2: Parse
    const topics = parseTopics(scrapeResult.markdown);
    
    if (topics.length === 0) {
      throw new Error('No topics found! Check parsing logic.');
    }
    
    // Step 3: Build hierarchy
    const hierarchicalTopics = buildHierarchy(topics);
    
    // Step 4: Upload
    const subject = await uploadToStaging(hierarchicalTopics, scrapeResult);
    
    // Step 5: Validate
    await validateData(subject.id);
    
    console.log('\n' + '='.repeat(50));
    console.log('✅ TEST COMPLETE!');
    console.log('\nNext steps:');
    console.log('1. Check Supabase staging_aqa.subjects table');
    console.log('2. Check Supabase staging_aqa.topics table');
    console.log('3. If data looks good, proceed to Day 2 (scale to all AQA subjects)');
    console.log('4. If issues found, debug and re-run');
    
  } catch (error) {
    console.error('\n❌ TEST FAILED:', error.message);
    console.error(error.stack);
    process.exit(1);
  }
}

// Run it!
main();

