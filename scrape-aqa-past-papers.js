/**
 * AQA Past Papers Scraper
 * 
 * Scrapes the AQA past papers search page to catalog:
 * - Question papers
 * - Mark schemes
 * - Examiner reports
 * 
 * Stores PDF URLs (doesn't download PDFs - just catalogs them)
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
  searchQuery: 'biology 7402' // Use subject code for precision
};

const YEARS_TO_SCRAPE = [2024, 2023, 2022, 2021, 2020]; // Last 5 years

// ================================================================
// STEP 1: SCRAPE PAST PAPERS PAGE
// ================================================================

async function scrapePastPapersPage() {
  console.log('🔍 Scraping AQA past papers for', SUBJECT.name);
  console.log(`   Search query: ${SUBJECT.searchQuery}`);
  
  const url = `https://www.aqa.org.uk/find-past-papers-and-mark-schemes?q=${encodeURIComponent(SUBJECT.searchQuery)}`;
  
  try {
    const result = await fc.scrapeUrl(url, {
      formats: ['markdown', 'html'],
      onlyMainContent: false  // We need the whole page for filters
    });
    
    console.log('✅ Scraped past papers page');
    console.log(`   Content length: ${result.markdown?.length || 0} chars`);
    
    // Save for debugging
    await fs.writeFile('debug-past-papers.md', result.markdown || '');
    await fs.writeFile('debug-past-papers.html', result.html || '');
    
    return result;
    
  } catch (error) {
    console.error('❌ Failed to scrape:', error.message);
    throw error;
  }
}

// ================================================================
// STEP 2: PARSE PAPER LINKS
// ================================================================

function parsePaperLinks(markdown, html) {
  console.log('\n📋 Parsing paper links...');
  
  const papers = [];
  
  // Extract all PDF links
  const linkPattern = /\[(.*?)\]\((https:\/\/cdn\.sanity\.io\/files\/[^)]+\.pdf[^)]*)\)/g;
  
  let match;
  while ((match = linkPattern.exec(markdown)) !== null) {
    const title = match[1];
    const url = match[2];
    
    // Parse the title
    const parsed = parsePaperTitle(title);
    
    if (parsed) {
      papers.push({
        ...parsed,
        url,
        title
      });
    }
  }
  
  console.log(`✅ Found ${papers.length} paper documents`);
  
  // Categorize
  const categorized = {
    questionPapers: papers.filter(p => p.type === 'question_paper'),
    markSchemes: papers.filter(p => p.type === 'mark_scheme'),
    examinerReports: papers.filter(p => p.type === 'examiner_report')
  };
  
  console.log(`   Question papers: ${categorized.questionPapers.length}`);
  console.log(`   Mark schemes: ${categorized.markSchemes.length}`);
  console.log(`   Examiner reports: ${categorized.examinerReports.length}`);
  
  return categorized;
}

function parsePaperTitle(title) {
  /**
   * Title patterns:
   * - "Biology - Mark scheme (Foundation) : Paper 1 Biology - June 2024"
   * - "Science - Question paper (Higher): Paper 1 Biology - June 2023"
   * - "Biology - Report on the exam: Paper 1 Biology - June 2022"
   */
  
  // Extract resource type
  let type = 'question_paper';
  if (title.toLowerCase().includes('mark scheme')) type = 'mark_scheme';
  if (title.toLowerCase().includes('report on the exam') || title.toLowerCase().includes('examiner')) {
    type = 'examiner_report';
  }
  
  // Extract tier (Foundation/Higher) - A-level has no tier
  let tier = null;
  const tierMatch = title.match(/\((Foundation|Higher)\)/i);
  if (tierMatch) tier = tierMatch[1];
  
  // Extract paper number
  const paperMatch = title.match(/Paper\s+(\d+)/i);
  const paperNumber = paperMatch ? parseInt(paperMatch[1]) : null;
  
  // Extract month and year
  const dateMatch = title.match(/(June|November|January|May)\s+(20\d{2})/i);
  if (!dateMatch) return null; // Skip if can't determine date
  
  const series = dateMatch[1];
  const year = parseInt(dateMatch[2]);
  
  return {
    type,
    tier,
    paperNumber,
    series,
    year
  };
}

// ================================================================
// STEP 3: GROUP PAPERS INTO COMPLETE SETS
// ================================================================

function groupPaperSets(categorized) {
  console.log('\n🗂️  Grouping into complete paper sets...');
  
  const sets = {};
  
  // Create a key for each unique paper
  const allPapers = [
    ...categorized.questionPapers,
    ...categorized.markSchemes,
    ...categorized.examinerReports
  ];
  
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
    
    // Add the appropriate URL
    if (paper.type === 'question_paper') sets[key].question_paper_url = paper.url;
    if (paper.type === 'mark_scheme') sets[key].mark_scheme_url = paper.url;
    if (paper.type === 'examiner_report') sets[key].examiner_report_url = paper.url;
  }
  
  const paperSets = Object.values(sets);
  
  console.log(`✅ Created ${paperSets.length} complete paper sets`);
  
  // Show distribution by year
  const byYear = {};
  paperSets.forEach(p => byYear[p.year] = (byYear[p.year] || 0) + 1);
  Object.keys(byYear).sort().reverse().forEach(year => {
    console.log(`   ${year}: ${byYear[year]} papers`);
  });
  
  return paperSets;
}

// ================================================================
// STEP 4: UPLOAD TO DATABASE
// ================================================================

async function uploadPapers(paperSets) {
  console.log('\n💾 Uploading papers to staging database...');
  
  try {
    // Get subject ID
    const { data: subject } = await supabase
      .from('staging_aqa_subjects')
      .select('id')
      .eq('subject_code', SUBJECT.code)
      .eq('qualification_type', SUBJECT.qualification)
      .single();
    
    if (!subject) {
      throw new Error('Subject not found! Run crawl-aqa-subject-complete.js first.');
    }
    
    // Check if exam_papers table exists
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
    
    // Try to insert
    try {
      // Clear existing papers for this subject
      await supabase
        .from('staging_aqa_exam_papers')
        .delete()
        .eq('subject_id', subject.id);
      
      const { data: inserted, error } = await supabase
        .from('staging_aqa_exam_papers')
        .insert(papersToInsert)
        .select();
      
      if (error) throw error;
      
      console.log(`✅ Uploaded ${inserted.length} paper sets to database`);
      
    } catch (dbError) {
      console.log('⚠️  Database table not ready, saving to JSON instead');
      
      await fs.mkdir('data/past-papers', { recursive: true });
      await fs.writeFile(
        `data/past-papers/${SUBJECT.code}-papers.json`,
        JSON.stringify(paperSets, null, 2)
      );
      
      console.log(`✅ Saved to data/past-papers/${SUBJECT.code}-papers.json`);
    }
    
  } catch (error) {
    console.error('❌ Upload failed:', error.message);
    throw error;
  }
}

// ================================================================
// MAIN
// ================================================================

async function main() {
  console.log('📄 AQA PAST PAPERS SCRAPER');
  console.log('='.repeat(60));
  
  try {
    // Step 1: Scrape past papers page
    const pageResult = await scrapePastPapersPage();
    
    // Step 2: Parse links
    const categorized = parsePaperLinks(pageResult.markdown, pageResult.html);
    
    // Step 3: Group into sets
    const paperSets = groupPaperSets(categorized);
    
    // Step 4: Upload
    await uploadPapers(paperSets);
    
    console.log('\n' + '='.repeat(60));
    console.log('✅ PAST PAPERS SCRAPING COMPLETE!');
    console.log(`\nCataloged papers for ${SUBJECT.name}:`);
    
    // Show summary
    const last5Years = paperSets.filter(p => p.year >= 2020);
    console.log(`   Last 5 years (2020-2024): ${last5Years.length} papers`);
    console.log(`   With mark schemes: ${last5Years.filter(p => p.mark_scheme_url).length}`);
    console.log(`   With examiner reports: ${last5Years.filter(p => p.examiner_report_url).length}`);
    
    console.log('\nNext: Scale this to all AQA subjects!');
    
  } catch (error) {
    console.error('\n❌ FAILED:', error.message);
    console.error(error.stack);
    process.exit(1);
  }
}

main();

