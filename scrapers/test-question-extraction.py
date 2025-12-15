"""
Test Question Extraction from Exam Papers
Uses same approach as your topic scrapers (pdfplumber + OpenAI)

Run: python test-question-extraction.py
"""

import os
import sys
import json
import requests
import base64
import io
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from supabase import create_client
from PIL import Image

# Load environment
env_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")
load_dotenv(env_path)

# Initialize Supabase
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_ANON_KEY')
supabase = create_client(supabase_url, supabase_key)

# Test paper
TEST_PAPER = {
    'name': 'OCR Biology A - June 2024 - Paper 3',
    'url': 'https://www.ocr.org.uk/Images/726692-question-paper-unified-biology.pdf',
    'expected_marks': 70,
}

def extract_pages_as_images(pdf_content: bytes) -> dict:
    """
    Convert each PDF page to full-page image
    This captures ALL content: text, diagrams, tables, charts, labels
    """
    try:
        import pdfplumber
        import io
        
        print("📄 Converting PDF pages to images...")
        
        page_images = []
        full_text = ""
        
        with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                # Extract text to detect end of questions
                page_text = page.extract_text() or ""
                full_text += f"\n--- PAGE {page_num} ---\n{page_text}"
                
                # Check if this is the end of questions
                if any(phrase in page_text for phrase in [
                    'END OF QUESTION PAPER',
                    'END OF QUESTIONS',
                    'EXTRA ANSWER SPACE',
                ]):
                    print(f"   ℹ️  Detected end of questions on page {page_num}")
                    break
                
                # Skip cover page only
                if page_num == 1:
                    print(f"   ⏭️  Skipping page 1 (cover)")
                    continue
                
                # Convert full page to image
                try:
                    print(f"   📸 Rendering page {page_num}...")
                    page_img = page.to_image(resolution=150)  # 150 DPI = good quality
                    
                    # Convert to base64
                    img_bytes = io.BytesIO()
                    page_img.save(img_bytes, format='PNG')
                    img_base64 = base64.b64encode(img_bytes.getvalue()).decode('utf-8')
                    
                    page_images.append({
                        'page': page_num,
                        'base64': img_base64,
                        'text_preview': page_text[:200]  # First 200 chars for reference
                    })
                    
                except Exception as img_err:
                    print(f"   ⚠️  Could not render page {page_num}: {img_err}")
            
            print(f"✅ Converted {len(page_images)} pages to images")
            print(f"✅ Extracted {len(full_text)} characters of text")
            
            return {
                'text': full_text,
                'page_images': page_images,
                'total_pages': len(pdf.pages),
                'question_pages': len(page_images)
            }
            
    except Exception as e:
        print(f"❌ PDF processing failed: {e}")
        return None

def extract_questions_with_openai(pdf_data: dict) -> list:
    """Use OpenAI GPT-4o Vision to extract and structure questions from full page images"""
    
    openai_key = os.getenv('OPENAI_API_KEY')
    if not openai_key:
        raise Exception("OPENAI_API_KEY not found in .env")
    
    client = OpenAI(api_key=openai_key)
    
    page_images = pdf_data['page_images']
    
    print(f"🤖 Sending to GPT-4o Vision ({len(page_images)} full pages)...")
    
    # Build content with all page images
    content = [
        {
            'type': 'text',
            'text': f"""You are an expert at extracting exam questions from exam papers.

Extract ALL questions from this OCR Biology A-Level exam paper.

I'm providing you with:
1. The full text of the paper (with page markers)
2. All images/graphs/diagrams from the paper

UNDERSTANDING QUESTION STRUCTURE:
Exam questions have a hierarchy:
- Main questions: 1, 2, 3, 4, 5, 6 (usually NO marks, just context)
- Sub-questions: 1(a), 1(b), 2(a), 2(b) (these have marks)
- Sub-sub-questions: 1(a)(i), 1(a)(ii), 2(b)(i) (these have marks)

Main questions provide CONTEXT/SCENARIO for all sub-questions below them.

MARKS FORMAT (look for both!):
- Square brackets: [4] or [4 marks] ← Most common
- Round brackets: (4) or (4 marks) ← Sometimes used
- At end of question or on separate line
- Extract the NUMBER only (not the word "marks")

For each question/sub-question that HAS MARKS, extract:

1. full_question_number: "1(a)(i)", "2(b)", "3(c)" etc (the complete identifier)
2. main_question_number: 1, 2, 3, 4, 5, or 6 (the main parent question)
3. question_text: The actual question being asked (ONLY the question, not context)
4. context_text: Background/scenario text from parent questions (if any)
5. marks: Number only (extract from [4] or (4 marks) - just the number)
6. command_word: First word of question (Describe, Explain, Calculate, State, Outline, Evaluate, etc.)
7. question_type: "multiple_choice", "short_answer", or "extended_response"
8. has_image: true if question references "the graph", "the diagram", "Fig. X shows", "the table", etc.
9. image_description: What the image shows (graph title, diagram content, etc.)
10. image_page: Which page number the image appears on

CRITICAL RULES:
- Extract EVERY question that has marks
- Don't extract main questions (1, 2, 3) that have no marks (they're just context)
- Include complete question text
- Capture context from parent questions
- Look at images to understand questions that reference them

Return your response as a JSON object with this structure:
{{
  "questions": [
    {{
      "full_question_number": "2(a)",
      "main_question_number": 2,
      "question_text": "Describe two improvements to the student's plan and explain why they would be improvements.",
      "context_text": "Species biodiversity is affected by many factors. A student plans to sample plant species in the area shown below...",
      "marks": 4,
      "command_word": "Describe",
      "question_type": "extended_response",
      "has_image": true,
      "image_description": "Diagram showing grassland with shrubs, bushes, and a river",
      "image_page": 5
    }},
    {{
      "full_question_number": "2(b)(i)",
      "main_question_number": 2,
      "question_text": "Outline the differences between the bird and mammal results shown in the graph.",
      "context_text": "The IUCN compiles a Red List. A 2016 study assessed threats to 3789 species...",
      "marks": 2,
      "command_word": "Outline",
      "question_type": "short_answer",
      "has_image": true,
      "image_description": "Bar graph showing threat categories for birds vs mammals",
      "image_page": 6
    }}
  ]
}}

I'm providing you with full-page images of the exam paper (pages 2-20).
Each image shows the complete page with ALL content: questions, diagrams, tables, graphs, and labels.

Look at the images carefully to extract all questions."""
        }
    ]
    
    # Add all page images (they contain everything)
    for page_img in page_images:
        content.append({
            'type': 'image_url',
            'image_url': {
                'url': f"data:image/png;base64,{page_img['base64']}"
            }
        })
    
    print(f"   📤 Sending {len(page_images)} full-page images...")

    try:
        response = client.chat.completions.create(
            model='gpt-4o',
            messages=[
                {'role': 'user', 'content': content}
            ],
            max_tokens=16000,
            response_format={'type': 'json_object'},
        )
        
        result_text = response.choices[0].message.content
        result = json.loads(result_text)
        
        questions = result.get('questions', [])
        
        print(f"✅ Extracted {len(questions)} questions")
        
        return {
            'questions': questions,
            'usage': {
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens,
            }
        }
        
    except Exception as e:
        print(f"❌ OpenAI extraction failed: {e}")
        raise

def parse_question_hierarchy(question_number: str) -> dict:
    """
    Parse question number into hierarchy components
    Examples:
      "1" → {main: 1, sub: None, sub_sub: None}
      "2(a)" → {main: 2, sub: "a", sub_sub: None}
      "3(b)(ii)" → {main: 3, sub: "b", sub_sub: "ii"}
    """
    import re
    
    # Pattern: number + optional (letter) + optional (roman)
    match = re.match(r'^(\d+)(?:\(([a-z])\))?(?:\(([ivx]+)\))?$', question_number.lower())
    
    if match:
        return {
            'main': int(match.group(1)),
            'sub': match.group(2),
            'sub_sub': match.group(3),
            'full': question_number
        }
    else:
        # Fallback
        return {
            'main': None,
            'sub': None,
            'sub_sub': None,
            'full': question_number
        }

def upload_images_to_storage(images: list, paper_id: str = 'test') -> list:
    """Upload extracted images to Supabase Storage"""
    
    print(f"\n📤 Uploading {len(images)} images to Supabase Storage...")
    
    uploaded_urls = []
    
    for img in images:
        try:
            # Create unique filename
            filename = f"{paper_id}_page{img['page']}_img{img['index']}.png"
            filepath = f"test/{filename}"
            
            # Decode base64 to bytes
            img_bytes = base64.b64decode(img['base64'])
            
            # Upload to Supabase Storage
            result = supabase.storage.from_('exam-images').upload(
                filepath,
                img_bytes,
                file_options={"content-type": "image/png", "upsert": "true"}
            )
            
            # Get public URL
            url_result = supabase.storage.from_('exam-images').get_public_url(filepath)
            public_url = url_result
            
            uploaded_urls.append({
                'page': img['page'],
                'url': public_url
            })
            
            print(f"   ✅ Uploaded image from page {img['page']}")
            
        except Exception as e:
            print(f"   ⚠️  Failed to upload image from page {img['page']}: {e}")
    
    print(f"✅ Uploaded {len(uploaded_urls)} images successfully")
    return uploaded_urls

def display_results(result):
    """Display extraction results with hierarchy"""
    questions = result['questions']
    
    print("\n" + "="*80)
    print("📊 EXTRACTION RESULTS")
    print("="*80)
    
    print(f"\n✅ Found {len(questions)} question parts\n")
    
    # Parse hierarchy for all questions
    for q in questions:
        hierarchy = parse_question_hierarchy(q.get('full_question_number') or q.get('question_number', ''))
        q['hierarchy'] = hierarchy
    
    # Group by main question
    by_main = {}
    for q in questions:
        main = q['hierarchy']['main']
        if main:
            if main not in by_main:
                by_main[main] = []
            by_main[main].append(q)
    
    print(f"📝 Main Questions: {len(by_main)}\n")
    
    # Show first 3 main questions with their parts
    for main_num in sorted(by_main.keys())[:3]:
        parts = by_main[main_num]
        print(f"\n{'='*80}")
        print(f"QUESTION {main_num} ({len(parts)} parts):")
        print('='*80)
        
        for q in parts:
            has_img = "📊" if q.get('has_image') else "  "
            indent = "  " * (bool(q['hierarchy']['sub']) + bool(q['hierarchy']['sub_sub']))
            
            q_num = q.get('full_question_number') or q.get('question_number')
            print(f"\n{indent}{has_img} {q_num}) {q['question_text'][:80]}...")
            print(f"{indent}   Marks: {q.get('marks', '?')} | Command: {q.get('command_word', '?')}")
            
            if q.get('context_text'):
                print(f"{indent}   📝 Context: {q['context_text'][:60]}...")
            
            if q.get('has_image') and q.get('image_description'):
                print(f"{indent}   🖼️  {q['image_description'][:60]}...")
    
    if len(questions) > 10:
        print(f"\n... and {len(questions) - 10} more questions")
    
    # Summary
    total_marks = sum(q.get('marks') or 0 for q in questions)
    questions_with_null_marks = [q for q in questions if q.get('marks') is None]
    
    command_words = {}
    for q in questions:
        cmd = q.get('command_word', 'Unknown')
        command_words[cmd] = command_words.get(cmd, 0) + 1
    
    print("\n" + "─"*80)
    print("\n📈 SUMMARY:")
    print(f"   Total Questions: {len(questions)}")
    print(f"   Total Marks: {total_marks} (Expected: {TEST_PAPER['expected_marks']})")
    print(f"   Match: {'✅' if total_marks == TEST_PAPER['expected_marks'] else '❌'}")
    
    questions_with_images = [q for q in questions if q.get('has_image')]
    print(f"   Questions with Images: {len(questions_with_images)}")
    
    if questions_with_null_marks:
        print(f"\n⚠️  {len(questions_with_null_marks)} questions have missing marks:")
        for q in questions_with_null_marks[:5]:
            print(f"      - Q{q['question_number']}: {q['question_text'][:60]}...")
    print(f"\n   Command Words:")
    for word, count in sorted(command_words.items()):
        print(f"   - {word}: {count}")
    
    print(f"\n💰 API Cost:")
    usage = result['usage']
    cost = (usage['prompt_tokens'] * 0.0025 / 1000) + (usage['completion_tokens'] * 0.01 / 1000)
    print(f"   Tokens: {usage['total_tokens']:,}")
    print(f"   Estimated: ${cost:.4f}")
    
    print("\n" + "="*80)

def save_results(result):
    """Save to JSON file"""
    output_dir = Path(__file__).parent / 'output'
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / 'test-extraction-results.json'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'paper': TEST_PAPER,
            'extraction': result,
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Results saved to: {output_file}")

def main():
    print("🧪 EXAM PAPER EXTRACTION TEST")
    print("="*80)
    print(f"\n📄 Test Paper: {TEST_PAPER['name']}")
    print(f"🔗 URL: {TEST_PAPER['url']}\n")
    
    try:
        # Download PDF
        print("⬇️  Downloading PDF...")
        response = requests.get(TEST_PAPER['url'])
        response.raise_for_status()
        pdf_content = response.content
        print(f"✅ Downloaded {len(pdf_content) / 1024:.1f} KB")
        
        # Convert pages to images (captures everything!)
        pdf_data = extract_pages_as_images(pdf_content)
        if not pdf_data:
            raise Exception("Failed to process PDF")
        
        print(f"\n📊 Processing {pdf_data['question_pages']} question pages (out of {pdf_data['total_pages']} total)")
        
        # Extract questions using full-page images (AI can see EVERYTHING!)
        result = extract_questions_with_openai(pdf_data)
        
        # Display
        display_results(result)
        
        # Save
        save_results(result)
        
        print("\n✅ Test complete!")
        print("\n📋 Next steps:")
        print("   1. Open the PDF and compare questions")
        print("   2. Check if all questions were found")
        print("   3. Verify marks and question text")
        print("   4. Share results for prompt refinement\n")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()

