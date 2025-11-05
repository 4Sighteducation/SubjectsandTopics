/**
 * Edexcel History A-Level Topic Scraper (PDF-Based)
 * Code: 9HI0 (2015 spec)
 * 
 * Tests Firecrawl PDF scraping with History!
 */

import Firecrawl from '@mendable/firecrawl-js';
import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';
import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';

// Get directory of current file
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Load .env from project root (4 levels up from this file)
dotenv.config({ path: path.join(__dirname, '../../../../.env') });

const fc = new Firecrawl({ apiKey: process.env.FIRECRAWL_API_KEY });
const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_KEY);

// ================================================================
// CONFIG: Edexcel History A-Level
// ================================================================

const SUBJECT = {
  name: 'History',
  code: '9HI0',  // Edexcel A-Level History code
  qualification: 'A-Level',
  exam_board: 'Edexcel',
  courseMaterialsUrl: 'https://qualifications.pearson.com/en/qualifications/edexcel-a-levels/history-2015.html',
  // Direct PDF URL (from Download button on course materials page)
  specificationPDF: 'https://qualifications.pearson.com/content/dam/pdf/A%20Level/History/2015/Specification%20and%20sample%20assessments/9781446914366-gce-2015-a-hist.pdf'
};

// ================================================================
// STEP 1: GET SPECIFICATION PDF URL
// ================================================================

function getSpecificationPDF() {
  console.log('📄 Using direct PDF URL...');
  console.log(`   URL: ${SUBJECT.specificationPDF}`);
  return SUBJECT.specificationPDF;
}

// ================================================================
// STEP 2: SCRAPE PDF WITH FIRECRAWL
// ================================================================

async function scrapePDFSpecification(pdfUrl) {
  console.log('\n📄 Scraping PDF specification...');
  console.log(`   URL: ${pdfUrl}`);
  console.log('   This may take 60-120 seconds (large PDF)...\n');
  
  const maxRetries = 2;
  let attempt = 0;
  
  while (attempt <= maxRetries) {
    try {
      if (attempt > 0) {
        console.log(`   Retry attempt ${attempt}/${maxRetries}...`);
      }
      
      const result = await fc.scrapeUrl(pdfUrl, {
        formats: ['markdown'],
        onlyMainContent: true,
        timeout: 120000  // 120 seconds timeout
      });
      
      const markdown = result.markdown || '';
      
      console.log(`✅ PDF scraped successfully!`);
      console.log(`   Content length: ${markdown.length} characters`);
      
      // Save raw markdown for debugging
      const debugPath = path.join(__dirname, '../../../../debug-edexcel-history-spec.md');
      await fs.writeFile(debugPath, markdown);
      console.log(`   Saved raw markdown to debug-edexcel-history-spec.md`);
      
      return markdown;
      
    } catch (error) {
      attempt++;
      if (attempt > maxRetries) {
        console.error('❌ PDF scraping failed after all retries:', error.message);
        throw error;
      }
      console.warn(`   ⚠️  Attempt ${attempt} failed: ${error.message}`);
      console.log(`   Waiting 5 seconds before retry...`);
      await new Promise(resolve => setTimeout(resolve, 5000));
    }
  }
}

// ================================================================
// STEP 3: PARSE TOPICS FROM PDF MARKDOWN
// ================================================================

function parseHistoryTopics(markdown) {
  console.log('\n📋 Parsing History topics from PDF...');
  
  const topics = [];
  const lines = markdown.split('\n');
  
  let currentRoute = null;      // Level 0: Route A, Route B, etc.
  let currentOption = null;     // Level 1: Option 1A, 2B.1, etc.
  let currentTheme = null;      // Level 2: Themes
  let buildingTheme = false;
  let themeLines = [];
  
  // Map option codes to their routes (we'll build this as we parse TOC)
  const optionToRoute = {};
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line) continue;
    
    // Pattern 0a: "Route X: Title" (may be multiline)
    const routeMatch = line.match(/^Route\s+([A-H]):\s+(.+)$/i);
    if (routeMatch) {
      const routeLetter = routeMatch[1];
      let routeTitle = routeMatch[2].trim();
      
      // Remove page number if present at end
      routeTitle = routeTitle.replace(/\s+\d+$/, '');
      
      // If no page number on this line, title continues on next line
      if (!routeMatch[2].match(/\d+$/) && i + 1 < lines.length) {
        const nextLine = lines[i + 1].trim();
        // Continuation line will have page number at end
        if (nextLine && nextLine.match(/\d+$/)) {
          routeTitle += ' ' + nextLine.replace(/\s+\d+$/, '');
          i++; // Skip next line
        }
      }
      
      const routeCode = `Route${routeLetter}`;
      
      // Only create route once (skip duplicates from repeated TOCs)
      const alreadyExists = topics.find(t => t.code === routeCode);
      if (!alreadyExists) {
        currentRoute = routeCode;
        
        topics.push({
          code: routeCode,
          title: `Route ${routeLetter}: ${routeTitle}`,
          level: 0,
          parentCode: null
        });
        
        console.log(`   Found ${routeCode}: ${routeTitle.substring(0, 50)}...`);
      } else {
        // Route already exists, just update currentRoute
        currentRoute = routeCode;
      }
      continue;
    }
    
    // Pattern 0b: "Knowledge, skills and understanding: Paper 3" (create Paper 3 container)
    if (line.match(/^Knowledge,\s+skills\s+and\s+understanding:\s+Paper\s+3/i)) {
      currentRoute = 'Paper3';
      
      topics.push({
        code: 'Paper3',
        title: 'Paper 3 Options',
        level: 0,
        parentCode: null
      });
      
      console.log(`   Found Paper 3 section`);
      continue;
    }
    
    // Pattern 1a: "Paper X, Option YZ:" (content section - title on next line)
    const paperOptionContentMatch = line.match(/^Paper\s+(\d+|3),\s+Option\s+([^:]+):$/i);
    if (paperOptionContentMatch) {
      const optionCode = paperOptionContentMatch[2].trim().replace(/\s+/g, '');
      
      // Title is on next line
      let optionTitle = '';
      if (i + 1 < lines.length) {
        optionTitle = lines[i + 1].trim();
        i++;
      }
      
      currentOption = `Option${optionCode}`;
      currentTheme = null;
      buildingTheme = false;
      
      // Get the route this option belongs to from our map
      const belongsToRoute = optionToRoute[currentOption];
      if (belongsToRoute) {
        currentRoute = belongsToRoute;
      }
      
      // If this option doesn't exist yet (wasn't in TOC), create it now!
      const optionExists = topics.find(t => t.code === currentOption);
      if (!optionExists && currentRoute) {
        topics.push({
          code: currentOption,
          title: `Option ${optionCode}: ${optionTitle}`,
          level: 1,
          parentCode: currentRoute
        });
        console.log(`   >> Created missing ${currentOption} under ${currentRoute}`);
      }
      
      console.log(`   >> Entering content for ${currentOption} [${currentRoute || 'unknown route'}]`);
      continue;
    }
    
    // Pattern 1b: "Paper X, Option YZ: Title PageNum" (table of contents)
    const paperOptionTOCMatch = line.match(/^Paper\s+(\d+|3),\s+Option\s+([^:]+):\s*(.+?)\s+\d+$/i);
    if (paperOptionTOCMatch) {
      const optionCode = paperOptionTOCMatch[2].trim().replace(/\s+/g, '');
      let optionTitle = paperOptionTOCMatch[3].trim();
      
      const optionKey = `Option${optionCode}`;
      
      // Map this option to current route
      if (currentRoute) {
        optionToRoute[optionKey] = currentRoute;
      }
      
      // Create option topic (Level 1, parent is current Route)
      topics.push({
        code: optionKey,
        title: `Option ${optionCode}: ${optionTitle}`,
        level: 1,
        parentCode: currentRoute
      });
      
      console.log(`   Found ${optionKey} under ${currentRoute}`);
      continue;
    }
    
    if (!currentOption) continue;
    
    // Pattern 2: Theme number (1-9) followed by text
    const themeMatch = line.match(/^([1-9])\s+(.+)$/);
    if (themeMatch) {
      const potentialThemeNum = themeMatch[1];
      const potentialText = themeMatch[2];
      
      // Filter out false positives (assessment rubrics, page numbers, etc.)
      const isFalsePositive = 
        line.match(/Level\s+\d+|Mark\s+Descriptor/i) ||
        potentialText.match(/^(No rewardable|Selects material|Attempts analysis|Explains analysis|Analyses, explains|Sustained analysis)/i) ||
        potentialText.length < 10;
      
      if (!isFalsePositive) {
        // Finalize previous theme if building one
        if (buildingTheme && themeLines.length > 0) {
          const prevThemeNum = themeLines[0].match(/^(\d+)/)[1];
          const prevThemeTitle = themeLines.join(' ').replace(/^\d+\s+/, '').trim();
          const code = `${currentOption}.${prevThemeNum}`;
          topics.push({
            code,
            title: `${prevThemeNum} ${prevThemeTitle}`,
            level: 2,
            parentCode: currentOption
          });
          currentTheme = code;
          console.log(`     Theme: ${prevThemeNum} ${prevThemeTitle.substring(0, 40)}...`);
        }
        
        // Start new theme
        buildingTheme = true;
        themeLines = [line];
        continue;
      }
    }
    
    // Pattern 3: Continuation of theme title OR finalize on bullet
    if (buildingTheme) {
      if (line.startsWith('●')) {
        // Finalize theme
        if (themeLines.length > 0) {
          const themeNum = themeLines[0].match(/^(\d+)/)[1];
          const themeTitle = themeLines.join(' ').replace(/^\d+\s+/, '').trim();
          const code = `${currentOption}.${themeNum}`;
          topics.push({
            code,
            title: `${themeNum} ${themeTitle}`,
            level: 2,
            parentCode: currentOption
          });
          currentTheme = code;
          console.log(`     Theme: ${themeNum} ${themeTitle.substring(0, 40)}...`);
        }
        buildingTheme = false;
        themeLines = [];
        // Fall through to process bullet
      } else if (!line.match(/^(Themes Content|Pearson Edexcel|Specification|^\d{1,3}$)/)) {
        // Continue building theme title (multiline)
        if (line.length > 0 && line.length < 150) {
          themeLines.push(line);
        }
        continue;
      }
    }
    
    // Pattern 4: Content bullets "● Text: details..."
    const bulletMatch = line.match(/^●\s+([^:]+):/);
    if (bulletMatch && currentTheme) {
      const contentTitle = bulletMatch[1].trim();
      
      // Filter out obvious non-topics
      if (contentTitle.length < 5 || contentTitle.length > 100) continue;
      if (contentTitle.match(/(Level|Mark|assessment|students|answer)/i)) continue;
      
      const contentCount = topics.filter(t => 
        t.parentCode === currentTheme && t.level === 3
      ).length;
      const code = `${currentTheme}.${contentCount + 1}`;
      
      topics.push({
        code,
        title: contentTitle,
        level: 3,
        parentCode: currentTheme
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
  
  // Show distribution
  const levels = {};
  unique.forEach(t => levels[t.level] = (levels[t.level] || 0) + 1);
  
  console.log('   Distribution:');
  Object.keys(levels).sort().forEach(l => {
    console.log(`   Level ${l}: ${levels[l]} topics`);
  });
  
  // Show sample hierarchy
  console.log('\n   Sample hierarchy:');
  const routeA = unique.find(t => t.code === 'RouteA');
  if (routeA) {
    console.log(`   ${routeA.title}`);
    const options = unique.filter(t => t.parentCode === 'RouteA').slice(0, 2);
    options.forEach(option => {
      console.log(`   ├─ ${option.title.substring(0, 60)}...`);
      const themes = unique.filter(t => t.parentCode === option.code).slice(0, 2);
      themes.forEach(theme => {
        console.log(`   │  ├─ ${theme.title.substring(0, 50)}...`);
        const content = unique.filter(t => t.parentCode === theme.code).slice(0, 2);
        content.forEach(c => {
          console.log(`   │  │  └─ ${c.title}`);
        });
      });
    });
  }
  
  return unique;
}

// ================================================================
// STEP 4: UPLOAD TO STAGING
// ================================================================

async function uploadToStaging(topics) {
  console.log('\n💾 Uploading to staging database...');
  
  try {
    // 1. Subject (with exam_board column!)
    const { data: subject, error: subjectError } = await supabase
      .from('staging_aqa_subjects')
      .upsert({
        subject_name: `${SUBJECT.name} (${SUBJECT.qualification})`,
        subject_code: SUBJECT.code,
        qualification_type: SUBJECT.qualification,
        specification_url: SUBJECT.courseMaterialsUrl,
        exam_board: SUBJECT.exam_board
      }, { onConflict: 'subject_code,qualification_type,exam_board' })
      .select()
      .single();
    
    if (subjectError) throw subjectError;
    console.log(`✅ Subject: ${subject.subject_name} [${SUBJECT.exam_board}]`);
    
    // 2. DELETE old topics (prevents duplicates!)
    await supabase
      .from('staging_aqa_topics')
      .delete()
      .eq('subject_id', subject.id);
    
    console.log(`✅ Cleared old topics (prevents duplicates)`);
    
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
    let missingParents = 0;
    const missingParentCodes = new Set();
    
    for (const topic of topics) {
      if (topic.parentCode) {
        const parentId = codeToId.get(topic.parentCode);
        const childId = codeToId.get(topic.code);
        
        if (!parentId) {
          missingParents++;
          missingParentCodes.add(topic.parentCode);
        }
        
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
    
    if (missingParents > 0) {
      console.log(`⚠️  ${missingParents} topics have missing parents:`);
      console.log(`   Missing parent codes: ${Array.from(missingParentCodes).join(', ')}`);
    }
    
    return subject.id;
  } catch (error) {
    console.error('❌ Upload failed:', error);
    throw error;
  }
}

// ================================================================
// STEP 5: VALIDATION
// ================================================================

async function validateData(subjectId) {
  console.log('\n📊 Validating History dataset...');
  
  const { data: allTopics } = await supabase
    .from('staging_aqa_topics')
    .select('*')
    .eq('subject_id', subjectId)
    .eq('exam_board', SUBJECT.exam_board)
    .order('topic_code');
  
  // Count by level
  const levels = {};
  allTopics.forEach(t => levels[t.topic_level] = (levels[t.topic_level] || 0) + 1);
  
  console.log(`   Total topics: ${allTopics.length}`);
  Object.keys(levels).sort().forEach(l => {
    console.log(`   Level ${l}: ${levels[l]} topics`);
  });
  
  // Sample
  console.log('\n📋 Sample topics (first 20):');
  allTopics.slice(0, 20).forEach(t => {
    const indent = '  '.repeat(t.topic_level);
    console.log(`   ${indent}${t.topic_code} - ${t.topic_name}`);
  });
  
  return allTopics.length;
}

// ================================================================
// MAIN
// ================================================================

async function main() {
  console.log('🚀 EDEXCEL HISTORY A-LEVEL - TOPIC SCRAPER (PDF)');
  console.log('='.repeat(60));
  console.log(`\nSubject: ${SUBJECT.name}`);
  console.log(`Code: ${SUBJECT.code}`);
  console.log(`Exam Board: ${SUBJECT.exam_board}`);
  console.log(`\nExpected hierarchy:`);
  console.log(`  Level 0: Routes (Route A-H, Paper 3)`);
  console.log(`  Level 1: Options (Option 1A, 2B.1, 30, etc.)`);
  console.log(`  Level 2: Themes (from table "Themes" column)`);
  console.log(`  Level 3: Content items (up to colon only)`);
  console.log('');
  
  try {
    // Step 1: Get PDF URL
    const pdfUrl = getSpecificationPDF();
    
    // Step 2: Scrape PDF
    const markdown = await scrapePDFSpecification(pdfUrl);
    
    // Step 3: Parse topics
    const topics = parseHistoryTopics(markdown);
    
    // Step 4: Upload to staging
    const subjectId = await uploadToStaging(topics);
    
    // Step 5: Validate
    const totalCount = await validateData(subjectId);
    
    console.log('\n' + '='.repeat(60));
    console.log('✅ EDEXCEL HISTORY - TOPICS COMPLETE!');
    console.log(`   Total topics: ${totalCount}`);
    console.log(`   Exam board: ${SUBJECT.exam_board}`);
    console.log('\n💡 Notes:');
    console.log('   - PDF-based scraping with Firecrawl');
    console.log('   - Can be re-run safely (deletes old data first)');
    console.log('   - Check debug-edexcel-history-spec.md for raw PDF content');
    console.log('\n📊 Check in Supabase:');
    console.log(`   SELECT * FROM staging_aqa_topics WHERE exam_board='Edexcel' AND subject_id='${subjectId}';`);
    console.log('\nNext: Review topics in Supabase, then run papers scraper');
    
  } catch (error) {
    console.error('\n❌ FAILED:', error.message);
    console.error(error.stack);
    process.exit(1);
  }
}

main();

