/**
 * AQA Past Papers Scraper - IMPROVED
 * 
 * Uses filter URLs to get all papers efficiently:
 * - Question papers
 * - Mark schemes
 * - Examiner reports
 * 
 * Handles pagination automatically
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
  qualification: 'A-level Biology',
  searchQuery: 'biology'  // Just subject name, filters handle the rest
};

const RESOURCE_TYPES = {
  questions: 'Question+papers',
  markSchemes: 'Mark+Schemes',
  reports: 'Examiners+reports'
};

// ================================================================
// STEP 1: BUILD FILTER URLS
// ================================================================

function buildFilterUrls() {
  const baseUrl = 'https://www.aqa.org.uk/find-past-papers-and-mark-schemes';
  
  // Use specCode parameter instead of search query - this is the key!
  const urls = {
    questionPapers: `${baseUrl}?qualification=${encodeURIComponent(SUBJECT.qualification)}&specCode=${SUBJECT.code}&secondaryResourceType=${RESOURCE_TYPES.questions}`,
    markSchemes: `${baseUrl}?qualification=${encodeURIComponent(SUBJECT.qualification)}&specCode=${SUBJECT.code}&secondaryResourceType=${RESOURCE_TYPES.markSchemes}`,
    examinerReports: `${baseUrl}?qualification=${encodeURIComponent(SUBJECT.qualification)}&specCode=${SUBJECT.code}&secondaryResourceType=${RESOURCE_TYPES.reports}`
  };
  
  return urls;
}

// ================================================================
// STEP 2: SCRAPE EACH FILTERED PAGE
// ================================================================

async function scrapeFilteredResults() {
  console.log('🔍 Scraping AQA past papers for', SUBJECT.name);
  console.log('='.repeat(60));
  
  const urls = buildFilterUrls();
  const results = {};
  
  // Scrape question papers
  console.log('\n📄 Scraping question papers...');
  console.log(`   URL: ${urls.questionPapers}`);
  const questionResult = await fc.scrapeUrl(urls.questionPapers, {
    formats: ['markdown', 'html'],
    onlyMainContent: false,  // Need full page to get JS-loaded content
    waitFor: 3000            // Wait for JS to load
  });
  results.questions = questionResult.markdown || '';
  console.log(`✅ Scraped (${questionResult.markdown?.length || 0} chars)`);
  
  // Scrape mark schemes
  console.log('\n📝 Scraping mark schemes...');
  console.log(`   URL: ${urls.markSchemes}`);
  const markSchemeResult = await fc.scrapeUrl(urls.markSchemes, {
    formats: ['markdown', 'html'],
    onlyMainContent: false,
    waitFor: 3000
  });
  results.markSchemes = markSchemeResult.markdown || '';
  console.log(`✅ Scraped (${markSchemeResult.markdown?.length || 0} chars)`);
  
  // Scrape examiner reports
  console.log('\n📊 Scraping examiner reports...');
  console.log(`   URL: ${urls.examinerReports}`);
  const reportResult = await fc.scrapeUrl(urls.examinerReports, {
    formats: ['markdown', 'html'],
    onlyMainContent: false,
    waitFor: 3000
  });
  results.reports = reportResult.markdown || '';
  console.log(`✅ Scraped (${reportResult.markdown?.length || 0} chars)`);
  
  // Save for debugging
  await fs.writeFile('debug-papers-questions.md', results.questions);
  await fs.writeFile('debug-papers-markschemes.md', results.markSchemes);
  await fs.writeFile('debug-papers-reports.md', results.reports);
  console.log('\n💾 Saved debug files');
  
  return results;
}

// ================================================================
// STEP 3: PARSE PAPER METADATA
// ================================================================

function parsePaperMetadata(markdown, resourceType) {
  const papers = [];
  
  // Pattern: [Title](PDF URL)
  const linkPattern = /\[(.*?)\]\((https:\/\/cdn\.sanity\.io\/files\/[^)]+\.pdf[^)]*)\)/g;
  
  let match;
  while ((match = linkPattern.exec(markdown)) !== null) {
    const title = match[1];
    const url = match[2];
    
    const parsed = parsePaperTitle(title, resourceType);
    
    if (parsed) {
      papers.push({
        ...parsed,
        url,
        rawTitle: title
      });
    }
  }
  
  return papers;
}

function parsePaperTitle(title, resourceType) {
  /**
   * Title patterns:
   * - "Biology - Examiner report: Paper 1 - June 2024"
   * - "Science - Examiners report (Foundation): Paper 1 Biology - June 2024"
   * - "Biology - Mark scheme (Higher) : Paper 2 Biology - June 2023"
   * - "Biology - Question paper: Paper 1 - June 2024"
   */
  
  // Extract tier
  let tier = null;
  const tierMatch = title.match(/\((Foundation|Higher)\)/i);
  if (tierMatch) tier = tierMatch[1];
  
  // Extract paper number
  const paperMatch = title.match(/Paper\s+(\d+)/i);
  const paperNumber = paperMatch ? parseInt(paperMatch[1]) : 1;
  
  // Extract date (month + year)
  const dateMatch = title.match(/(June|November|January|May)\s+(20\d{2})/i);
  if (!dateMatch) return null;
  
  const series = dateMatch[1];
  const year = parseInt(dateMatch[2]);
  
  // Determine type
  let type = resourceType;
  if (title.toLowerCase().includes('question paper')) type = 'question_paper';
  if (title.toLowerCase().includes('mark scheme')) type = 'mark_scheme';
  if (title.toLowerCase().includes('examiner')) type = 'examiner_report';
  
  return {
    type,
    tier,
    paperNumber,
    series,
    year
  };
}

// ================================================================
// STEP 4: GROUP INTO COMPLETE SETS
// ================================================================

function groupIntoSets(questionPapers, markSchemes, reports) {
  console.log('\n🗂️  Grouping papers into complete sets...');
  
  const sets = {};
  
  // Combine all papers
  const allPapers = [
    ...questionPapers.map(p => ({ ...p, docType: 'question' })),
    ...markSchemes.map(p => ({ ...p, docType: 'mark' })),
    ...reports.map(p => ({ ...p, docType: 'report' }))
  ];
  
  // Group by year/series/tier/paper
  for (const paper of allPapers) {
    const key = `${paper.year}-${paper.series}-${paper.tier || 'A-Level'}-P${paper.paperNumber}`;
    
    if (!sets[key]) {
      sets[key] = {
        year: paper.year,
        series: paper.series,
        tier: paper.tier,
        paperNumber: paper.paperNumber,
        question_paper_url: null,
        mark_scheme_url: null,
        examiner_report_url: null
      };
    }
    
    // Add URL based on document type
    if (paper.docType === 'question') sets[key].question_paper_url = paper.url;
    if (paper.docType === 'mark') sets[key].mark_scheme_url = paper.url;
    if (paper.docType === 'report') sets[key].examiner_report_url = paper.url;
  }
  
  const paperSets = Object.values(sets);
  
  console.log(`✅ Created ${paperSets.length} complete paper sets`);
  
  // Show breakdown
  const byYear = {};
  paperSets.forEach(p => byYear[p.year] = (byYear[p.year] || 0) + 1);
  
  console.log('   By year:');
  Object.keys(byYear).sort().reverse().forEach(year => {
    const yearPapers = paperSets.filter(p => p.year === parseInt(year));
    const withMark = yearPapers.filter(p => p.mark_scheme_url).length;
    const withReport = yearPapers.filter(p => p.examiner_report_url).length;
    console.log(`   ${year}: ${byYear[year]} papers (${withMark} with marks, ${withReport} with reports)`);
  });
  
  return paperSets;
}

// ================================================================
// STEP 5: UPLOAD TO DATABASE
// ================================================================

async function uploadPapers(paperSets) {
  console.log('\n💾 Uploading to staging database...');
  
  try {
    // Get subject ID
    const { data: subject } = await supabase
      .from('staging_aqa_subjects')
      .select('id')
      .eq('subject_code', SUBJECT.code)
      .eq('qualification_type', SUBJECT.qualification.includes('A-level') ? 'A-Level' : 'GCSE')
      .single();
    
    if (!subject) {
      throw new Error('Subject not found! Run crawl-aqa-subject-complete.js first.');
    }
    
    // Delete existing papers for this subject
    await supabase
      .from('staging_aqa_exam_papers')
      .delete()
      .eq('subject_id', subject.id);
    
    // Insert papers
    const papersToInsert = paperSets.map(p => ({
      subject_id: subject.id,
      year: p.year,
      exam_series: p.series,
      paper_number: p.paperNumber,
      tier: p.tier,
      question_paper_url: p.question_paper_url,
      mark_scheme_url: p.mark_scheme_url,
      examiner_report_url: p.examiner_report_url
    }));
    
    const { data: inserted, error } = await supabase
      .from('staging_aqa_exam_papers')
      .insert(papersToInsert)
      .select();
    
    if (error) throw error;
    
    console.log(`✅ Uploaded ${inserted.length} paper sets`);
    
    return inserted;
    
  } catch (error) {
    console.error('❌ Upload failed:', error.message);
    
    // Fallback: save to JSON
    await fs.mkdir('data/past-papers', { recursive: true });
    await fs.writeFile(
      `data/past-papers/${SUBJECT.code}-papers.json`,
      JSON.stringify(paperSets, null, 2)
    );
    console.log(`💾 Saved to data/past-papers/${SUBJECT.code}-papers.json instead`);
  }
}

// ================================================================
// MAIN
// ================================================================

async function main() {
  console.log('📄 AQA PAST PAPERS SCRAPER (Improved)');
  console.log('='.repeat(60));
  
  try {
    // Step 1: Scrape filtered results
    const scraped = await scrapeFilteredResults();
    
    // Step 2: Parse each type
    console.log('\n📋 Parsing documents...');
    const questionPapers = parsePaperMetadata(scraped.questions, 'question_paper');
    const markSchemes = parsePaperMetadata(scraped.markSchemes, 'mark_scheme');
    const reports = parsePaperMetadata(scraped.reports, 'examiner_report');
    
    console.log(`   Question papers: ${questionPapers.length}`);
    console.log(`   Mark schemes: ${markSchemes.length}`);
    console.log(`   Examiner reports: ${reports.length}`);
    
    // Step 3: Group into complete sets
    const paperSets = groupIntoSets(questionPapers, markSchemes, reports);
    
    // Step 4: Upload to database
    await uploadPapers(paperSets);
    
    console.log('\n' + '='.repeat(60));
    console.log('✅ PAST PAPERS CATALOGING COMPLETE!');
    console.log(`\n${SUBJECT.name} (${SUBJECT.code}):`);
    console.log(`   Total paper sets: ${paperSets.length}`);
    
    // Show last 5 years
    const last5 = paperSets.filter(p => p.year >= 2020);
    console.log(`   Last 5 years (2020-2024): ${last5.length} papers`);
    console.log(`   Complete sets (all 3 documents): ${last5.filter(p => 
      p.question_paper_url && p.mark_scheme_url && p.examiner_report_url
    ).length}`);
    
    console.log('\nNext: Scale to all AQA subjects!');
    
  } catch (error) {
    console.error('\n❌ FAILED:', error.message);
    console.error(error.stack);
    process.exit(1);
  }
}

main();

