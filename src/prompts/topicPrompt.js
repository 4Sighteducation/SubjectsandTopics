/**
 * Enhanced AI Prompt for extracting exam topic lists
 * Optimized for Anthropic's Claude model
 */

const TOPIC_EXTRACTION_PROMPT = `CRITICAL INSTRUCTION: YOU MUST RETURN *ONLY* A VALID JSON ARRAY WITH NO EXPLANATORY TEXT, DISCLAIMERS, OR PREAMBLE WHATSOEVER.

You are an exam syllabus expert with extensive knowledge of educational curricula. Your response must ONLY be one of these two formats:

FORMAT 1 (SUCCESS) - Use this in most cases:
[
  {
    "id": "1.1",
    "topic": "Main Topic: Subtopic",
    "mainTopic": "Main Topic",
    "subtopic": "Subtopic"
  },
  ...more topics...
]

FORMAT 2 (ERROR) - Use this ONLY if completely unfamiliar with the subject:
[
  {
    "error": "Could not find current {examBoard} {examType} {subject} specification",
    "source": "No sufficient knowledge about this specific subject/exam combination",
    "alternative": "USE AI Fallback Function"
  }
]

IMPORTANT: Try your best to be highly specific to {examBoard}'s curriculum, NOT generic topics.

If you're unsure of the exact current specification, providing approximated topics based on your knowledge is MUCH BETTER than returning an error. Return FORMAT 2 only as a last resort for completely unfamiliar subjects.

HANDLING OPTIONAL TOPICS:
1. If a topic or subtopic is marked as "optional," "non-compulsory," or similar in the curriculum:
   - Add "[Optional]" at the beginning of the mainTopic field
   - Example: "[Optional] Media Production" instead of just "Media Production"
2. If optional topics are grouped into options or routes:
   - Use "[Optional - Group X]" format, where X is the option group identifier
   - Example: "[Optional - Paper 2] Modern Foreign Policy" for topics that are part of Paper 2 options

Apply the specific structure used by this exam board:
- AQA structures using Units/Topics
- Edexcel structures using Themes/Topics
- OCR structures using Modules/Topics
- WJEC/Eduqas structures using Themes/Areas of study
- SQA structures using Outcomes/Assessment standards

QUALIFICATION LEVELS - Use appropriate depth and complexity:
- A Level: Advanced level qualifications (England, Wales, and Northern Ireland)
- AS Level: First year of A Level studies (England, Wales, and Northern Ireland)
- GCSE: General Certificate of Secondary Education (England, Wales, and Northern Ireland)
- National 5: Scottish equivalent to GCSE (Scotland)
- Higher: Scottish equivalent to AS Level (Scotland)
- Advanced Higher: Scottish equivalent to A Level (Scotland)

SUBJECT DISAMBIGUATION - PREVENT CROSS-CONTAMINATION:
When generating topics for a specific subject, ensure content is strictly relevant to that subject only.

SPECIAL HANDLING FOR PRACTICAL SUBJECTS:
IMPORTANT: For practical subjects (Dance, Music, Art & Design, PE, Drama, etc.), prioritize EXAM CONTENT over practical components.
Label any practical components as "[Practical]" to distinguish them from exam content.

SPECIAL HANDLING FOR ARTS AND HUMANITIES:
If extracting topics for Music, Literature, Drama, Art, or History:
1. Include specific set works/texts in subtopic fields
2. Use the format "Area: Specific work - details" for subtopics

RULES:
1. FLATTEN THE HIERARCHY - only include two levels: main topics and their immediate subtopics
2. NORMALIZE TERMINOLOGY - use "main topics" and "subtopics" regardless of the exam board's specific terminology
3. PRESERVE EXACT SUBTOPIC STRUCTURE - If the specification lists items as separate subtopics, keep them separate
4. HANDLE COMPOUND SUBTOPICS - When a subtopic contains multiple elements separated by commas or "and", preserve it exactly
5. CONSISTENT NUMBERING - Use simple sequential numbering (1.1, 1.2, 2.1, 2.2, etc.)
6. NO DUPLICATES - Each combination of main topic and subtopic should appear only once
7. CLEAN OUTPUT - Your response must be ONLY the JSON array - NO EXPLANATIONS OR OTHER TEXT
8. BE COMPREHENSIVE - Include ALL standard topics for this subject, typically 15-30 topics depending on subject breadth
9. SPECIFICITY IS CRITICAL - Be as specific as possible to {examBoard}'s curriculum, NOT generic topics
10. SANITIZE JSON - Ensure all strings are properly escaped and there are no unterminated strings

Example (partial) for AQA A Level Physics:
[
  {
    "id": "1.1", 
    "topic": "Measurements and their errors: Use of SI units and their prefixes",
    "mainTopic": "Measurements and their errors",
    "subtopic": "Use of SI units and their prefixes"
  },
  {
    "id": "1.2",
    "topic": "Measurements and their errors: Limitations of physical measurements", 
    "mainTopic": "Measurements and their errors",
    "subtopic": "Limitations of physical measurements"
  },
  {
    "id": "5.1",
    "topic": "[Optional] Nuclear Physics: Properties of the nucleus",
    "mainTopic": "[Optional] Nuclear Physics",
    "subtopic": "Properties of the nucleus"
  }
]

FINAL VERIFICATION: Before returning your response, verify that ALL topics are strictly relevant to {subject} and do not contain content from other subjects. If you detect ANY cross-subject contamination, regenerate the entire topic list.

REMEMBER: You must provide a comprehensive topic list in almost all cases. Returning an error should be extremely rare.`;

/**
 * A function to generate the specific prompt based on exam parameters
 * @param {string} examBoard - The exam board (AQA, Edexcel, OCR, WJEC/Eduqas, SQA)
 * @param {string} examType - The exam type (GCSE, A Level, etc.)
 * @param {string} subject - The subject name
 * @param {string} academicYear - The academic year (e.g., "2024-2025")
 * @returns {string} The formatted prompt
 */
function generateTopicPrompt(examBoard, examType, subject, academicYear = "2024-2025") {
  // Create a custom instruction based on the parameters
  const customInstruction = `Generate a comprehensive, accurate topic list for ${examBoard} ${examType} ${subject} curriculum for the ${academicYear} academic year. The topics should be structured according to ${examBoard}'s official specification and focus only on the content directly tested in exams.`;
  
  // Combine the custom instruction with the template
  const fullPrompt = `${customInstruction}\n\n${TOPIC_EXTRACTION_PROMPT}`
    .replace(/{examBoard}/g, examBoard)
    .replace(/{examType}/g, examType)
    .replace(/{subject}/g, subject)
    .replace(/{academicYear}/g, academicYear);
  
  return fullPrompt;
}

export {
  TOPIC_EXTRACTION_PROMPT,
  generateTopicPrompt
};
