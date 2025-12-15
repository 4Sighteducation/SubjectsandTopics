"""
Test Examiner Report Extraction
Extract insights from examiner reports

Run: python test-examiner-report-extraction.py
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

# Test examiner report
TEST_REPORT = {
    'name': 'OCR Biology A - June 2024 - Paper 3 - Examiner Report',
    'url': 'https://www.ocr.org.uk/Images/726425-examiners-report-unified-biology.pdf',
}

def extract_pages_as_images(pdf_content: bytes) -> dict:
    """Convert PDF pages to images"""
    try:
        import pdfplumber
        
        print("📄 Converting examiner report pages to images...")
        
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

def extract_insights_with_openai(report_data: dict) -> dict:
    """Extract examiner insights using GPT-4o Vision"""
    
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    page_images = report_data['page_images']
    
    print(f"🤖 Sending to GPT-4o Vision ({len(page_images)} pages)...")
    
    content = [
        {
            'type': 'text',
            'text': """You are an expert at analyzing examiner reports.

Extract insights from this OCR Biology A-Level examiner report.

Examiner reports contain:
- General commentary on how students performed
- Question-by-question analysis
- Common errors students made
- Examples of good answers
- Advice for future students

For each question mentioned in the report, extract:

1. question_number: "1(a)(i)", "2(b)", etc.
2. average_performance: "poor", "satisfactory", "good", "excellent"
3. common_errors: Array of mistakes students commonly made
4. good_practice: Array of things strong students did well
5. advice_for_students: Actionable advice for improving
6. examiner_comments: Key quotes from the report

Return your response as a JSON object:
{
  "general_comments": "Overall students performed...",
  "question_insights": [
    {
      "question_number": "1(a)(i)",
      "average_performance": "good",
      "common_errors": [
        "Many students wrote 'organelle' instead of the specific name",
        "Some confused ribosomes with mitochondria"
      ],
      "good_practice": [
        "Strong students specified '70S ribosome'",
        "Best answers were concise and precise"
      ],
      "advice_for_students": "Learn the specific names of cell structures, not just general terms",
      "examiner_comments": "This was generally well answered with most students achieving the mark."
    }
  ]
}

I'm providing full-page images of the examiner report."""
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
            'insights': result,
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
    """Display examiner insights"""
    insights = result['insights']
    question_insights = insights.get('question_insights', [])
    
    print("\n" + "="*80)
    print("📊 EXAMINER REPORT EXTRACTION RESULTS")
    print("="*80)
    
    if insights.get('general_comments'):
        print(f"\n📝 General Comments:")
        print(f"   {insights['general_comments'][:200]}...\n")
    
    print(f"✅ Found insights for {len(question_insights)} questions\n")
    
    # Show first 3
    for insight in question_insights[:3]:
        print(f"\n{'='*80}")
        print(f"QUESTION {insight['question_number']}")
        print('='*80)
        
        print(f"\n📊 Performance: {insight.get('average_performance', 'N/A')}")
        
        if insight.get('common_errors'):
            print(f"\n❌ Common Errors ({len(insight['common_errors'])}):")
            for err in insight['common_errors'][:2]:
                print(f"   • {err}")
        
        if insight.get('good_practice'):
            print(f"\n✅ Good Practice ({len(insight['good_practice'])}):")
            for prac in insight['good_practice'][:2]:
                print(f"   • {prac}")
        
        if insight.get('advice_for_students'):
            print(f"\n💡 Advice: {insight['advice_for_students'][:100]}...")
    
    print("\n" + "─"*80)
    print("\n📈 SUMMARY:")
    print(f"   Questions with insights: {len(question_insights)}")
    
    print(f"\n💰 API Cost:")
    usage = result['usage']
    cost = (usage['prompt_tokens'] * 0.0025 / 1000) + (usage['completion_tokens'] * 0.01 / 1000)
    print(f"   Tokens: {usage['total_tokens']:,}")
    print(f"   Estimated: ${cost:.4f}")
    
    print("\n" + "="*80)

def save_results(result):
    """Save results"""
    output_dir = Path(__file__).parent / 'output'
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / 'test-examiner-report-results.json'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'report': TEST_REPORT,
            'extraction': result,
        }, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Results saved to: {output_file}")

def main():
    print("🧪 EXAMINER REPORT EXTRACTION TEST")
    print("="*80)
    print(f"\n📄 Test Report: {TEST_REPORT['name']}")
    print(f"🔗 URL: {TEST_REPORT['url']}\n")
    
    try:
        # Download
        print("⬇️  Downloading examiner report PDF...")
        response = requests.get(TEST_REPORT['url'])
        response.raise_for_status()
        pdf_content = response.content
        print(f"✅ Downloaded {len(pdf_content) / 1024:.1f} KB")
        
        # Convert to images
        report_data = extract_pages_as_images(pdf_content)
        if not report_data:
            raise Exception("Failed to process PDF")
        
        print(f"\n📊 Processing {len(report_data['page_images'])} pages")
        
        # Extract insights
        result = extract_insights_with_openai(report_data)
        
        # Display
        display_results(result)
        
        # Save
        save_results(result)
        
        print("\n✅ Test complete!")
        print("\n📋 Next steps:")
        print("   1. Compare with actual examiner report")
        print("   2. Check insight quality")
        print("   3. Verify all questions covered\n")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()

