/**
 * Edexcel GCSE Science (Combined Science) - Topic Scraper
 * Code: 1SC0
 * 
 * Uses Firecrawl to convert PDF → clean markdown
 * Then parses topics from structured markdown
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
// CONFIG: GCSE Science (Combined Science)
// ================================================================

const SUBJECT = {
  name: 'Science (Combined Science)',
  code: 'GCSE-Science',
  qualification: 'GCSE',
  exam_board: 'Edexcel',
  specificationPDF: 'https://qualifications.pearson.com/content/dam/pdf/GCSE/Science/2016/Specification/gcse-combinedscience-spec.pdf'
};

// ================================================================
// STEP 1: SCRAPE PDF WITH FIRECRAWL
// ================================================================

async function scrapePDF() {
  console.log('\n📄 Scraping GCSE Science specification PDF...');
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
        onlyMainContent: true,
        timeout: 180000  // 3 minutes for large PDF
      });
      
      const markdown = result.markdown || '';
      
      console.log(`✅ PDF scraped successfully!`);
      console.log(`   Content length: ${markdown.length} characters`);
      
      // Save for debugging
      const debugPath = path.join(__dirname, 'debug-gcse-science-spec.md');
      await fs.writeFile(debugPath, markdown);
      console.log(`   Saved to debug-gcse-science-spec.md`);
      
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
// STEP 2: PARSE SCIENCE TOPICS
// ================================================================

function parseScienceTopics(markdown) {
  console.log('\n📋 Parsing Science topics...');
  
  const topics = [];
  const lines = markdown.split('\n');
  
  // Level 0: Papers (6 papers total)
  // Level 1: Topics (extracted from each paper's content overview)
  // Level 2: Students should items (numbered 1.1, 1.2, etc.)
  // Level 3: Lettered sub-items (a, b, c, etc.)
  
  // Step 1: Create the 6 papers from the assessment structure
  const papers = [
    { code: 'Paper1', title: 'Paper 1: Biology 1 (1SC0/1BF, 1SC0/1BH)', level: 0, parentCode: null },
    { code: 'Paper2', title: 'Paper 2: Biology 2 (1SC0/2BF, 1SC0/2BH)', level: 0, parentCode: null },
    { code: 'Paper3', title: 'Paper 3: Chemistry 1 (1SC0/1CF, 1SC0/1CH)', level: 0, parentCode: null },
    { code: 'Paper4', title: 'Paper 4: Chemistry 2 (1SC0/2CF, 1SC0/2CH)', level: 0, parentCode: null },
    { code: 'Paper5', title: 'Paper 5: Physics 1 (1SC0/1PF, 1SC0/1PH)', level: 0, parentCode: null },
    { code: 'Paper6', title: 'Paper 6: Physics 2 (1SC0/2PF, 1SC0/2PH)', level: 0, parentCode: null }
  ];
  
  topics.push(...papers);
  console.log(`[OK] Created ${papers.length} papers (Level 0)`);
  
  // Step 2: Extract topics for each paper from "Content overview" sections
  let currentPaper = null;
  let currentTopic = null;
  let currentNumberedItem = null;
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line) continue;
    
    // Skip obvious noise
    if (line.match(/^Pearson Edexcel|^©|^Specification.*Issue|^Assessment overview|^Written examination/i)) {
      continue;
    }
    
    // Pattern 1: Detect which paper we're in
    // "| Paper 1: Biology 1 (*Paper code: 1SC0/1BF, 1SC0/1BH) |" or without pipes
    const paperMatch = line.match(/Paper\s+(\d+):\s+(Biology|Chemistry|Physics)\s+[12]/i);
    if (paperMatch) {
      const paperNum = paperMatch[1];
      const subject = paperMatch[2];
      currentPaper = `Paper${paperNum}`;
      currentTopic = null; // Reset topic when entering new paper
      console.log(`\n[INFO] Processing ${currentPaper} (${subject})`);
      continue;
    }
    
    // Pattern 2: Extract topics from Content overview (ONLY if we're in a paper)
    if (currentPaper && line.match(/Content overview|^\|\s*Topic\s+\d+\s+[-–]/i)) {
      let contentText = line;
      
      // If this line has "Content overview" but no topics, grab next line
      if (line.match(/Content overview/i) && !line.match(/Topic\s+\d+/)) {
        if (i + 1 < lines.length) {
          contentText += ' ' + lines[i + 1].trim();
          i++; // Skip next line
        }
      }
      
      // Remove table pipes and clean
      contentText = contentText.replace(/^\||\|$/g, '').trim();
      
      // Extract all "Topic X – Name" or "Topic X - Name" patterns
      const topicMatches = contentText.matchAll(/Topic\s+(\d+)\s+[-–]\s+([^,|]+?)(?:,|$)/gi);
      
      for (const match of topicMatches) {
        const topicNum = match[1];
        let topicName = match[2].trim();
        
        // Clean up trailing noise
        topicName = topicName.replace(/\s*(Assessment|Content|overview)\s*$/gi, '').trim();
        
        if (!topicName || topicName.length < 5) continue;
        
        // Create unique code for this topic within this paper
        const code = `${currentPaper}_Topic${topicNum}`;
        
        // Check if already exists (avoid duplicates)
        if (topics.find(t => t.code === code)) continue;
        
        topics.push({
          code,
          title: `Topic ${topicNum} – ${topicName}`,
          level: 1,
          parentCode: currentPaper
        });
        
        console.log(`   [OK] ${code}: ${topicName.substring(0, 50)}...`);
      }
      
      continue;
    }
    
    // Pattern 3: Detect topic detail sections
    // "# Topic 1 – Key concepts in biology" (as a heading before tables)
    const topicHeadingMatch = line.match(/^#*\s*Topic\s+(\d+)\s+[–-]\s+(.+)$/i);
    if (topicHeadingMatch) {
      const topicNum = topicHeadingMatch[1];
      const topicName = topicHeadingMatch[2].trim();
      
      // Find which paper(s) contain this topic by searching through existing topics
      const matchingTopics = topics.filter(t => 
        t.level === 1 && t.title.includes(`Topic ${topicNum}`)
      );
      
      if (matchingTopics.length > 0) {
        // Use the first matching topic's code as current
        currentTopic = matchingTopics[0].code;
        console.log(`   [INFO] Parsing details for ${currentTopic}`);
      } else {
        // Create a fallback (shouldn't happen if content overview was parsed)
        currentTopic = `Topic${topicNum}`;
        console.log(`   [WARN] Topic ${topicNum} not found in papers, using fallback`);
      }
      continue;
    }
    
    if (!currentTopic) continue;
    
    // Pattern 4: Numbered items from "Students should:" markdown table (Level 2)
    // Table format: "| 1.1 | Explain how... | ... |"
    // Or plain: "1.1 Explain how..."
    
    // Try table format first
    let numberedMatch = line.match(/^\|\s*(\d+)\.(\d+)\s*\|\s*(.+?)\s*\|/);
    if (!numberedMatch) {
      // Try plain format
      numberedMatch = line.match(/^(\d+)\.(\d+)\s+(.+)$/);
    }
    
    if (numberedMatch) {
      const major = numberedMatch[1];
      const minor = numberedMatch[2];
      let content = numberedMatch[3].trim();
      
      // Remove any trailing pipes or empty cells
      content = content.replace(/\|\s*$/g, '').trim();
      
      // CRITICAL: Check if this line contains a lettered item from PREVIOUS numbered item
      // Example: "| 1.2 | c bacteria... Describe how..." where "c" belongs to 1.1
      const startsWithLetter = content.match(/^([a-z])\s+(.+?)(?:\s+[A-Z]|$)/);
      if (startsWithLetter && currentNumberedItem) {
        // This is actually a Level 3 item from the previous numbered item!
        const letter = startsWithLetter[1];
        const letteredContent = startsWithLetter[2].trim();
        
        const letteredCode = `${currentNumberedItem}_${letter}`;
        topics.push({
          code: letteredCode,
          title: letteredContent,
          level: 3,
          parentCode: currentNumberedItem
        });
        
        // Now extract the actual 1.2 content (after the lettered part)
        const afterLetter = content.substring(startsWithLetter[0].length).trim();
        if (afterLetter.length > 10) {
          content = afterLetter;
        } else {
          // The whole line was the lettered item, skip creating 1.2
          continue;
        }
      }
      
      // CRITICAL: Stop BEFORE any remaining lettered sub-items (a, b, c)
      // If content still contains lettered items, split it
      const hasLettered = content.match(/\s+([a-z])\s+/);
      if (hasLettered) {
        // Cut off before the first lettered item
        const cutPoint = content.indexOf(hasLettered[0]);
        content = content.substring(0, cutPoint).trim();
      }
      
      // Look ahead ONLY for continuation of the main description (NOT lettered items)
      let j = i + 1;
      while (j < lines.length && j < i + 5) {
        const nextLine = lines[j].trim();
        
        // Stop at next numbered item
        if (nextLine.match(/^\|?\s*\d+\.\d+/)) {
          break;
        }
        
        // Stop at lettered items (these are Level 3, not continuations!)
        if (nextLine.match(/^\|?\s*\|\s*[a-z]\s+/i) || nextLine.match(/^[a-z]\s+/i)) {
          break;
        }
        
        // Stop at table separators or headers
        if (nextLine.match(/^\|?\s*[-–]+\s*\|/) || nextLine.match(/^(Students should|Maths skills|Topic|#)/i)) {
          break;
        }
        
        // Stop at empty lines
        if (!nextLine) break;
        
        // Only merge if it's truly a continuation (no lettered items)
        if (nextLine.match(/^\|\s*\|\s*(.+?)\s*\|/)) {
          const contMatch = nextLine.match(/^\|\s*\|\s*(.+?)\s*\|/);
          if (contMatch && !contMatch[1].match(/^[a-z]\s/i)) {
            content += ' ' + contMatch[1].trim();
          } else {
            break; // Hit a lettered item, stop here
          }
        }
        
        j++;
      }
      
      const code = `${currentTopic}_${major}.${minor}`;
      currentNumberedItem = code;
      
      topics.push({
        code,
        title: content,
        level: 2,
        parentCode: currentTopic
      });
      
      i = j - 1; // Skip merged lines
      continue;
    }
    
    // Pattern 5: Lettered sub-items (Level 3)
    // Table format: "| | a animal cells – nucleus... | ... |"
    // Or plain: "a animal cells..."
    
    let letteredMatch = line.match(/^\|\s*\|\s*([a-z])\s+(.+?)\s*\|/);
    if (!letteredMatch) {
      letteredMatch = line.match(/^\|\s*([a-z])\s+(.+?)\s*\|/);
    }
    if (!letteredMatch) {
      letteredMatch = line.match(/^([a-z])\s+(.+)$/);
    }
    
    if (letteredMatch && currentNumberedItem) {
      const letter = letteredMatch[1].toLowerCase();
      let content = letteredMatch[2].trim();
      
      // Remove trailing pipes
      content = content.replace(/\|\s*$/g, '').trim();
      
      // Look ahead for continuations
      let j = i + 1;
      while (j < lines.length && j < i + 5) {
        const nextLine = lines[j].trim();
        
        // Stop at next item
        if (nextLine.match(/^[a-z]\s+/i) || nextLine.match(/^\d+\.\d+/)) {
          break;
        }
        
        // Stop at table separators or new sections
        if (nextLine.match(/^\|?\s*[-–]+\s*\|/) || nextLine.match(/^(Students|Topic|#)/i)) {
          break;
        }
        
        if (!nextLine) break;
        
        // Merge if it's a continuation row
        if (nextLine.match(/^\|\s*\|\s*(.+?)\s*\|/)) {
          const contMatch = nextLine.match(/^\|\s*\|\s*(.+?)\s*\|/);
          if (contMatch && !contMatch[1].match(/^[a-z]\s/)) {
            content += ' ' + contMatch[1].trim();
          }
        }
        
        j++;
      }
      
      const code = `${currentNumberedItem}_${letter}`;
      
      topics.push({
        code,
        title: content,
        level: 3,
        parentCode: currentNumberedItem
      });
      
      i = j - 1;
      continue;
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
  console.log('=' * 80);
  console.log('🚀 GCSE SCIENCE (COMBINED SCIENCE) - TOPIC SCRAPER');
  console.log('=' * 80);
  console.log(`\nSubject: ${SUBJECT.name}`);
  console.log(`Code: ${SUBJECT.code}`);
  console.log(`Exam Board: ${SUBJECT.exam_board}`);
  console.log(`\nExpected hierarchy:`);
  console.log(`  Level 0: Papers (1, 2)`);
  console.log(`  Level 1: Topics (Topic 1-22 across Bio/Chem/Phys)`);
  console.log(`  Level 2: Sub-topics (1.1, 1.2, etc.)`);
  console.log(`  Level 3: Learning outcomes`);
  console.log('');
  
  try {
    // Step 1: Scrape PDF
    const markdown = await scrapePDF();
    
    // Step 2: Parse topics
    const topics = parseScienceTopics(markdown);
    
    // Step 3: Upload
    const subjectId = await uploadToStaging(topics);
    
    console.log('\n' + '='.repeat(80));
    console.log('✅ GCSE SCIENCE - TOPICS COMPLETE!');
    console.log('='.repeat(80));
    console.log(`   Total topics: ${topics.length}`);
    console.log(`   Exam board: ${SUBJECT.exam_board}`);
    console.log('\n💡 Next: Review topics in Supabase data viewer');
    console.log('   Then we can extract the pattern into templates!');
    
  } catch (error) {
    console.error('\n❌ FAILED:', error.message);
    console.error(error.stack);
    process.exit(1);
  }
}

main();

