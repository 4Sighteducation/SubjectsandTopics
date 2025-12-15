"""
Test Mark Scheme Extraction
Extract marking points from mark scheme PDFs

Run: python test-mark-scheme-extraction.py
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

# Load environment
env_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")
load_dotenv(env_path)

# Test mark scheme (matches the question paper we tested)
TEST_MARK_SCHEME = {
    'name': 'OCR Biology A - June 2024 - Paper 3 - Mark Scheme',
    'url': 'https://www.ocr.org.uk/Images/726819-mark-scheme-unified-biology.pdf',
    'paper_url': 'https://www.ocr.org.uk/Images/726692-question-paper-unified-biology.pdf',
    'expected_questions': 29,  # From our question extraction test
}

def extract_pages_as_images(pdf_content: bytes) -> dict:
    """Convert PDF pages to images"""
    try:
        import pdfplumber
        
        print("📄 Converting mark scheme pages to images...")
        
        page_images = []
        full_text = ""
        
        with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                page_text = page.extract_text() or ""
                full_text += f"\n--- PAGE {page_num} ---\n{page_text}"
                
                # Skip cover
                if page_num == 1:
                    print(f"   ⏭️  Skipping page 1 (cover)")
                    continue
                
                # Render page
                print(f"   📸 Rendering page {page_num}...")
                page_img = page.to_image(resolution=150)
                
                img_bytes = io.BytesIO()
                page_img.save(img_bytes, format='PNG')
                img_base64 = base64.b64encode(img_bytes.getvalue()).decode('utf-8')
                
                page_images.append({
                    'page': page_num,
                    'base64': img_base64,
                })
            
            print(f"✅ Converted {len(page_images)} pages to images")
            
            return {
                'text': full_text,
                'page_images': page_images,
                'total_pages': len(pdf.pages)
            }
            
    except Exception as e:
        print(f"❌ Failed: {e}")
        return None

def extract_mark_scheme_with_openai(ms_data: dict) -> dict:
    """Extract marking points from mark scheme using GPT-4o Vision"""
    
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    page_images = ms_data['page_images']
    
    print(f"🤖 Sending to GPT-4o Vision ({len(page_images)} pages)...")
    
    content = [
        {
            'type': 'text',
            'text': """You are an expert at extracting mark schemes from exam papers.

Extract the marking points for EVERY question from this mark scheme.

Mark schemes show acceptable answers and how marks are awarded.

For each question, extract:

1. question_number: "1(a)(i)", "2(b)", etc.
2. max_marks: Total marks available
3. marking_points: Array of acceptable answers
   - Each point has: answer text, marks, keywords, alternatives
4. levels: For extended response questions (if present)
5. examiner_notes: Any additional guidance

MARKING POINT TYPES:

Type A - Specific answers (most common):
- "Ribosome" = 1 mark
- Accept: "70S ribosome", "Ribosome / 70S ribosome"
- Keywords: ribosome, 70S

Type B - Level-based (extended response):
- Level 1 (1-2 marks): Basic understanding
- Level 2 (3-4 marks): Clear explanation
- Level 3 (5-6 marks): Detailed analysis

Type C - Points-based (6 mark questions):
- Point 1: [description] = 1 mark
- Point 2: [description] = 1 mark
- Max 6 from: [list of possible points]

Return your response as a JSON object:
{
  "mark_schemes": [
    {
      "question_number": "1(a)(i)",
      "max_marks": 1,
      "marking_type": "specific",
      "marking_points": [
        {
          "answer": "Ribosome",
          "marks": 1,
          "keywords": ["ribosome", "70S"],
          "alternatives": ["70S ribosome"],
          "notes": "Accept either term"
        }
      ],
      "levels": null,
      "examiner_notes": null
    },
    {
      "question_number": "2(a)",
      "max_marks": 4,
      "marking_type": "points",
      "marking_points": [
        {
          "point": "Increase sample size",
          "marks": 1,
          "keywords": ["more", "increase", "sample"],
          "explanation": "More samples = more representative"
        },
        {
          "point": "Use stratified sampling",
          "marks": 1,
          "keywords": ["stratified", "proportional"],
          "explanation": "Ensures coverage of different habitats"
        }
      ],
      "levels": null,
      "examiner_notes": "Max 2 improvements, each with explanation"
    }
  ]
}

I'm providing full-page images of the mark scheme. Look carefully at all pages."""
        }
    ]
    
    # Add page images
    for page_img in page_images:
        content.append({
            'type': 'image_url',
            'image_url': {'url': f"data:image/png;base64,{page_img['base64']}"}
        })
    
    try:
        response = client.chat.completions.create(
            model='gpt-4o',
            messages=[{'role': 'user', 'content': content}],
            max_tokens=16000,
            response_format={'type': 'json_object'},
        )
        
        result = json.loads(response.choices[0].message.content)
        
        return {
            'mark_schemes': result.get('mark_schemes', []),
            'usage': {
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens,
            }
        }
        
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        raise

def display_results(result):
    """Display mark scheme extraction results"""
    mark_schemes = result['mark_schemes']
    
    print("\n" + "="*80)
    print("📊 MARK SCHEME EXTRACTION RESULTS")
    print("="*80)
    
    print(f"\n✅ Found marking guidance for {len(mark_schemes)} questions\n")
    
    # Show first 5 mark schemes
    for i, ms in enumerate(mark_schemes[:5], 1):
        print(f"\n{'='*80}")
        print(f"QUESTION {ms['question_number']} ({ms['max_marks']} marks)")
        print('='*80)
        
        print(f"\nMarking Type: {ms.get('marking_type', 'unknown')}")
        
        if ms.get('marking_points'):
            print(f"\nMarking Points ({len(ms['marking_points'])} points):")
            for j, point in enumerate(ms['marking_points'][:3], 1):
                if 'answer' in point:
                    print(f"  {j}. {point['answer']} ({point.get('marks', '?')} mark)")
                    if point.get('keywords'):
                        print(f"     Keywords: {', '.join(point['keywords'])}")
                elif 'point' in point:
                    print(f"  {j}. {point['point']} ({point.get('marks', '?')} mark)")
                    
        if ms.get('examiner_notes'):
            print(f"\n📝 Examiner notes: {ms['examiner_notes'][:100]}...")
    
    if len(mark_schemes) > 5:
        print(f"\n... and {len(mark_schemes) - 5} more mark schemes")
    
    # Summary
    total_marks = sum(ms.get('max_marks', 0) for ms in mark_schemes)
    
    print("\n" + "─"*80)
    print("\n📈 SUMMARY:")
    print(f"   Questions with marking: {len(mark_schemes)}")
    print(f"   Expected questions: {TEST_MARK_SCHEME['expected_questions']}")
    print(f"   Coverage: {len(mark_schemes)/TEST_MARK_SCHEME['expected_questions']*100:.1f}%")
    print(f"   Total marks: {total_marks}")
    
    print(f"\n💰 API Cost:")
    usage = result['usage']
    cost = (usage['prompt_tokens'] * 0.0025 / 1000) + (usage['completion_tokens'] * 0.01 / 1000)
    print(f"   Tokens: {usage['total_tokens']:,}")
    print(f"   Estimated: ${cost:.4f}")
    
    print("\n" + "="*80)

def save_results(result):
    """Save results to JSON"""
    output_dir = Path(__file__).parent / 'output'
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / 'test-mark-scheme-results.json'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'mark_scheme': TEST_MARK_SCHEME,
            'extraction': result,
        }, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Results saved to: {output_file}")

def main():
    print("🧪 MARK SCHEME EXTRACTION TEST")
    print("="*80)
    print(f"\n📄 Test Mark Scheme: {TEST_MARK_SCHEME['name']}")
    print(f"🔗 URL: {TEST_MARK_SCHEME['url']}\n")
    
    try:
        # Download
        print("⬇️  Downloading mark scheme PDF...")
        response = requests.get(TEST_MARK_SCHEME['url'])
        response.raise_for_status()
        pdf_content = response.content
        print(f"✅ Downloaded {len(pdf_content) / 1024:.1f} KB")
        
        # Convert to images
        ms_data = extract_pages_as_images(pdf_content)
        if not ms_data:
            raise Exception("Failed to process PDF")
        
        print(f"\n📊 Processing {len(ms_data['page_images'])} pages")
        
        # Extract mark schemes
        result = extract_mark_scheme_with_openai(ms_data)
        
        # Display
        display_results(result)
        
        # Save
        save_results(result)
        
        print("\n✅ Test complete!")
        print("\n📋 Next steps:")
        print("   1. Compare with actual mark scheme PDF")
        print("   2. Check if all questions covered")
        print("   3. Verify marking points are correct")
        print("   4. Share results for refinement\n")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()

