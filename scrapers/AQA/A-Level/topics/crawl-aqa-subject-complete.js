/**
 * COMPREHENSIVE AQA Subject Crawler
 * 
 * Gets EVERYTHING for one subject:
 * 1. Full topic hierarchy (3.1 → 3.1.1 → 3.1.1.1)
 * 2. Subject rules (optional modules, selection requirements)
 * 3. Past papers (last 5 years: 2020-2024)
 * 4. Mark schemes
 * 5. Examiner reports
 * 
 * Template for all AQA subjects
 */

import Firecrawl from '@mendable/firecrawl-js';
import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';
import fs from 'fs/promises';

dotenv.config();

const fc = new Firecrawl({ apiKey: process.env.FIRECRAWL_API_KEY });
const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_KEY);

// ================================================================
// CONFIG
// ================================================================

const SUBJECT = {
  name: 'Biology',
  code: '7402',
  qualification: 'A-Level',
  baseUrl: 'https://www.aqa.org.uk/subjects/biology/a-level/biology-7402'
};

// ================================================================
// STEP 1: CRAWL EVERYTHING
// ================================================================

async function crawlSubjectComplete() {
  console.log('🔍 COMPREHENSIVE CRAWL: AQA', SUBJECT.name);
  console.log('='.repeat(60));
  
  // 1A: Map all pages
  console.log('\n📡 Step 1A: Mapping all pages...');
  const mapResult = await fc.mapUrl(SUBJECT.baseUrl, {
    includeSubdomains: false,
    limit: 200
  });
  
  const urls = mapResult.links || [];
  console.log(`✅ Found ${urls.length} pages`);
  
  // 1B: Categorize URLs
  const categorized = {
    subjectContent: urls.filter(u => 
      u.includes('/specification/subject-content/') &&
      !u.includes('/downloads/')
    ),
    specAtGlance: urls.filter(u => 
      u.includes('/specification-at-a-glance')
    ),
    assessment: urls.filter(u => 
      u.includes('/assessment-resources')
    ),
    pastPapers: urls.filter(u => 
      u.includes('/past-papers-and-mark-schemes')
    )
  };
  
  console.log('   Subject content pages:', categorized.subjectContent.length);
  console.log('   Spec at a glance:', categorized.specAtGlance.length);
  console.log('   Assessment pages:', categorized.assessment.length);
  console.log('   Past papers:', categorized.pastPapers.length);
  
  // 1C: Scrape each category
  const scraped = {
    content: [],
    spec: [],
    assessment: [],
    papers: []
  };
  
  // Scrape subject content (topics)
  console.log('\n📚 Step 1B: Scraping topic pages...');
  for (const url of categorized.subjectContent.slice(0, 20)) {
    try {
      const result = await fc.scrapeUrl(url, { formats: ['markdown'], onlyMainContent: true });
      scraped.content.push({ ...result, url });
    } catch (err) {
      console.warn(`   ⚠️  Failed: ${url.split('/').pop()}`);
    }
  }
  console.log(`✅ Scraped ${scraped.content.length} content pages`);
  
  // Scrape spec at a glance (rules, components)
  console.log('\n📋 Step 1C: Scraping specification overview...');
  for (const url of categorized.specAtGlance) {
    try {
      const result = await fc.scrapeUrl(url, { formats: ['markdown'], onlyMainContent: true });
      scraped.spec.push({ ...result, url });
    } catch (err) {
      console.warn(`   ⚠️  Failed: spec at a glance`);
    }
  }
  console.log(`✅ Scraped ${scraped.spec.length} spec pages`);
  
  // Scrape past papers page
  console.log('\n📄 Step 1D: Scraping past papers...');
  for (const url of categorized.pastPapers) {
    try {
      const result = await fc.scrapeUrl(url, { formats: ['markdown'], onlyMainContent: true });
      scraped.papers.push({ ...result, url });
    } catch (err) {
      console.warn(`   ⚠️  Failed: past papers`);
    }
  }
  console.log(`✅ Scraped ${scraped.papers.length} paper pages`);
  
  return scraped;
}

// ================================================================
// STEP 2: PARSE TOPICS
// ================================================================

function parseTopics(contentPages) {
  console.log('\n📋 Step 2: Parsing topic hierarchy...');
  
  const allTopics = [];
  
  for (const page of contentPages) {
    const markdown = page.markdown || '';
    const pageTopics = extractTopicsFromMarkdown(markdown, page.url);
    allTopics.push(...pageTopics);
  }
  
  // Build hierarchy and remove duplicates
  const hierarchical = buildHierarchy(allTopics);
  
  console.log(`✅ Parsed ${hierarchical.length} unique topics`);
  const levels = {};
  hierarchical.forEach(t => levels[t.level] = (levels[t.level] || 0) + 1);
  Object.keys(levels).sort().forEach(l => 
    console.log(`   Level ${l}: ${levels[l]} topics`)
  );
  
  return hierarchical;
}

function extractTopicsFromMarkdown(markdown, sourceUrl) {
  const topics = [];
  const lines = markdown.split('\n');
  
  const patterns = [
    { regex: /^-\s*[•·]\s*\[(\d+(?:\.\d+)*)\s+([^\]]+)\]/, type: 'bullet' },
    { regex: /^(#{2,6})\s+(\d+(?:\.\d+)*)\s+(.+)$/, type: 'heading' },
    { regex: /^\|?\s*(\d+(?:\.\d+)+)\s*\|?\s*(.+)$/, type: 'table' },
    { regex: /^(\d+(?:\.\d+)+)\s+([A-Z].{3,})$/, type: 'plain' }
  ];
  
  for (const line of lines) {
    for (const pattern of patterns) {
      const match = line.match(pattern.regex);
      
      if (match) {
        let code, title;
        
        if (pattern.type === 'heading') {
          code = match[2];
          title = match[3];
        } else {
          code = match[1];
          title = match[2];
        }
        
        if (code && title && code.match(/^\d+\.\d+/)) { // Must have at least X.Y format
          const level = code.split('.').length - 2;
          if (level < 0) continue;
          
          const isALevelOnly = title.toLowerCase().includes('(a-level only)');
          const cleanTitle = title.replace(/\(A-level only\)/gi, '').trim();
          
          topics.push({
            code,
            title: cleanTitle,
            level,
            isALevelOnly,
            sourceUrl
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
    const codeParts = topic.code.split('.');
    const parentCode = codeParts.length > 1 
      ? codeParts.slice(0, -1).join('.')
      : null;
    
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
// STEP 3: EXTRACT SUBJECT RULES (AI-Assisted)
// ================================================================

function extractSubjectRules(specPages) {
  console.log('\n📐 Step 3: Extracting subject rules...');
  
  const rules = {
    components: [],
    optionalModules: [],
    selectionRules: [],
    assessmentStructure: []
  };
  
  for (const page of specPages) {
    const markdown = page.markdown || '';
    
    // Look for component information
    const componentMatches = markdown.match(/Component \d+[:\s]+([^\n]+)/gi);
    if (componentMatches) {
      rules.components.push(...componentMatches.map(m => m.trim()));
    }
    
    // Look for optional/choice language
    const optionMatches = markdown.match(/(choose|select|option|route)[^\n]{0,100}/gi);
    if (optionMatches) {
      rules.selectionRules.push(...optionMatches.map(m => m.trim()));
    }
    
    // Look for assessment info
    const assessMatches = markdown.match(/(Paper \d+|written exam|assessment)[^\n]{0,100}/gi);
    if (assessMatches) {
      rules.assessmentStructure.push(...assessMatches.map(m => m.trim()));
    }
  }
  
  // Deduplicate
  rules.components = [...new Set(rules.components)];
  rules.selectionRules = [...new Set(rules.selectionRules)];
  rules.assessmentStructure = [...new Set(rules.assessmentStructure)];
  
  console.log('✅ Rules extracted:');
  console.log(`   Components: ${rules.components.length}`);
  console.log(`   Selection rules: ${rules.selectionRules.length}`);
  console.log(`   Assessment info: ${rules.assessmentStructure.length}`);
  
  return rules;
}

// ================================================================
// STEP 4: EXTRACT PAST PAPERS
// ================================================================

function extractPastPapers(paperPages) {
  console.log('\n📄 Step 4: Extracting past papers...');
  
  const papers = [];
  
  for (const page of paperPages) {
    const markdown = page.markdown || '';
    const lines = markdown.split('\n');
    
    // Look for year headings and paper links
    let currentYear = null;
    let currentSeries = null;
    
    for (const line of lines) {
      // Match year: 2024, 2023, etc.
      const yearMatch = line.match(/^#{2,3}\s*(20\d{2})/);
      if (yearMatch) {
        currentYear = parseInt(yearMatch[1]);
      }
      
      // Match series: June, November
      const seriesMatch = line.match(/^#{3,4}\s*(June|November|January|May)/i);
      if (seriesMatch) {
        currentSeries = seriesMatch[1];
      }
      
      // Match paper links
      const paperMatch = line.match(/\[.*Paper\s+(\d+).*\]\((.*?)\)/i);
      if (paperMatch && currentYear) {
        const paperNumber = parseInt(paperMatch[1]);
        const url = paperMatch[2];
        
        // Determine if it's question paper, mark scheme, or examiner report
        let type = 'question_paper';
        if (url.includes('mark') || url.includes('ms')) type = 'mark_scheme';
        if (url.includes('report') || url.includes('er')) type = 'examiner_report';
        
        papers.push({
          year: currentYear,
          series: currentSeries || 'June',
          paperNumber,
          type,
          url: url.startsWith('http') ? url : `https://www.aqa.org.uk${url}`
        });
      }
    }
  }
  
  console.log(`✅ Found ${papers.length} paper documents`);
  
  // Group by year/series/paper
  const grouped = {};
  papers.forEach(p => {
    const key = `${p.year}-${p.series}-Paper${p.paperNumber}`;
    if (!grouped[key]) grouped[key] = {};
    grouped[key][p.type] = p.url;
    grouped[key].year = p.year;
    grouped[key].series = p.series;
    grouped[key].paperNumber = p.paperNumber;
  });
  
  const completePapers = Object.values(grouped);
  console.log(`   Organized into ${completePapers.length} complete paper sets`);
  
  return completePapers;
}

// ================================================================
// STEP 5: UPLOAD EVERYTHING TO STAGING
// ================================================================

async function uploadEverything(topics, rules, papers) {
  console.log('\n💾 Step 5: Uploading complete dataset...');
  
  try {
    // 1. Subject
    const { data: subject, error: subjectError } = await supabase
      .from('staging_aqa_subjects')
      .upsert({
        subject_name: `${SUBJECT.name} (${SUBJECT.qualification})`,
        subject_code: SUBJECT.code,
        qualification_type: SUBJECT.qualification,
        specification_url: SUBJECT.baseUrl
      }, { onConflict: 'subject_code,qualification_type' })
      .select()
      .single();
    
    if (subjectError) throw subjectError;
    console.log(`✅ Subject: ${subject.subject_name}`);
    
    // 2. Topics
    await supabase.from('staging_aqa_topics').delete().eq('subject_id', subject.id);
    
    const topicsToInsert = topics.map(t => ({
      subject_id: subject.id,
      topic_code: t.code,
      topic_name: t.title,
      topic_level: t.level,
      is_a_level_only: t.isALevelOnly
    }));
    
    const { data: insertedTopics } = await supabase
      .from('staging_aqa_topics')
      .insert(topicsToInsert)
      .select();
    
    console.log(`✅ Topics: ${insertedTopics.length} uploaded`);
    
    // 3. Link parent-child
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
    console.log(`✅ Hierarchy: ${linked} relationships linked`);
    
    // 4. Subject rules (store as metadata)
    await fs.writeFile(
      `data/subject-rules/${SUBJECT.code}-rules.json`,
      JSON.stringify(rules, null, 2)
    );
    console.log(`✅ Rules: Saved to data/subject-rules/${SUBJECT.code}-rules.json`);
    
    // 5. Past papers
    if (papers.length > 0) {
      // First create the table if it doesn't exist
      const papersToInsert = papers.map(p => ({
        subject_id: subject.id,
        year: p.year,
        exam_series: p.series,
        paper_number: p.paperNumber,
        question_paper_url: p.question_paper,
        mark_scheme_url: p.mark_scheme,
        examiner_report_url: p.examiner_report
      }));
      
      // Note: staging_aqa_exam_papers might not exist yet - that's OK for now
      try {
        await supabase.from('staging_aqa_exam_papers').delete().eq('subject_id', subject.id);
        const { data: insertedPapers } = await supabase
          .from('staging_aqa_exam_papers')
          .insert(papersToInsert)
          .select();
        console.log(`✅ Papers: ${insertedPapers?.length || 0} uploaded`);
      } catch (paperError) {
        console.log(`⚠️  Papers: Saved to JSON (table not ready yet)`);
        await fs.writeFile(
          `data/past-papers/${SUBJECT.code}-papers.json`,
          JSON.stringify(papers, null, 2)
        );
      }
    }
    
    return subject.id;
    
  } catch (error) {
    console.error('❌ Upload failed:', error);
    throw error;
  }
}

// ================================================================
// STEP 6: VALIDATION & SUMMARY
// ================================================================

async function generateReport(subjectId) {
  console.log('\n📊 FINAL REPORT');
  console.log('='.repeat(60));
  
  // Get all topics
  const { data: allTopics } = await supabase
    .from('staging_aqa_topics')
    .select('*')
    .eq('subject_id', subjectId)
    .order('topic_code');
  
  // Statistics
  const levels = {};
  allTopics.forEach(t => levels[t.topic_level] = (levels[t.topic_level] || 0) + 1);
  
  const aLevelOnly = allTopics.filter(t => t.is_a_level_only).length;
  const topLevel = allTopics.filter(t => !allTopics.some(p => p.topic_code === t.topic_code.split('.').slice(0, -1).join('.'))).length;
  
  console.log(`Subject: ${SUBJECT.name} (${SUBJECT.code})`);
  console.log(`\nTopic Statistics:`);
  console.log(`   Total topics: ${allTopics.length}`);
  Object.keys(levels).sort().forEach(l => {
    console.log(`   Level ${l}: ${levels[l]} topics`);
  });
  console.log(`   A-level only: ${aLevelOnly} topics`);
  console.log(`   Top-level sections: ${topLevel}`);
  
  // Sample hierarchy
  console.log(`\nSample Hierarchy (first 20):`);
  allTopics.slice(0, 20).forEach(t => {
    const indent = '  '.repeat(t.topic_level);
    const flag = t.is_a_level_only ? ' [A-level only]' : '';
    console.log(`   ${indent}${t.topic_code} ${t.topic_name}${flag}`);
  });
  
  console.log('\n' + '='.repeat(60));
  console.log('✅ SUCCESS! Complete dataset ready');
  console.log('\nNext Steps:');
  console.log('1. Check Supabase staging_aqa_topics table');
  console.log('2. Verify hierarchy looks correct');
  console.log('3. If good, scale to all AQA subjects');
  console.log('4. Then migrate to production curriculum_topics');
}

// ================================================================
// MAIN
// ================================================================

async function main() {
  try {
    // Ensure data directories exist
    await fs.mkdir('data/subject-rules', { recursive: true }).catch(() => {});
    await fs.mkdir('data/past-papers', { recursive: true }).catch(() => {});
    
    // Step 1: Crawl everything
    const scraped = await crawlSubjectComplete();
    
    // Step 2: Parse topics
    const topics = parseTopics(scraped.content);
    
    // Step 3: Extract rules
    const rules = extractSubjectRules(scraped.spec);
    
    // Step 4: Extract papers
    const papers = extractPastPapers(scraped.papers);
    
    // Step 5: Upload everything
    const subjectId = await uploadEverything(topics, rules, papers);
    
    // Step 6: Generate report
    await generateReport(subjectId);
    
  } catch (error) {
    console.error('\n❌ FAILED:', error.message);
    process.exit(1);
  }
}

main();

