"""Quick check of extracted Computer Science topics."""
import json
from pathlib import Path

# Check the latest report
report_file = Path(__file__).parent / "reports" / "Computer-Science-report.json"

if report_file.exists():
    with open(report_file, 'r', encoding='utf-8') as f:
        report = json.load(f)
    
    print("="*80)
    print("COMPUTER SCIENCE EXTRACTION REPORT")
    print("="*80)
    print(f"Success: {report.get('success', False)}")
    print(f"Total topics extracted: {report.get('topics_extracted', 0)}")
    print(f"\nTopics by level:")
    for level, count in sorted(report.get('levels', {}).items()):
        print(f"  Level {level}: {count} topics")
    
    print(f"\nWarnings: {report.get('warnings', [])}")
    print(f"Issues: {report.get('issues', [])}")
    
    print("\n" + "="*80)
    print("EXPECTED STRUCTURE (from PDF):")
    print("="*80)
    print("""
Component 1: Programming and System Development (should have ~9 main topics)
  1. Data structures
  2. Logical operations  
  3. Algorithms and programs
  4. Principles of programming
  5. Systems analysis
  6. System design
  7. Software engineering
  8. Program construction
  9. Economic, moral, legal, ethical and cultural issues

Component 2: Computer Architecture, Data, Communication and Applications (~9 topics)
  1. Hardware and communication
  2. Data transmission
  3. Data representation and data structures
  4. Organisation and structure of data
  5. The use of computer systems
  6. Database systems
  7. The operating system
  8. Data security and integrity processes
  9. Artificial intelligence (AI)

Component 3: Programmed Solution to a Problem (NEA - minimal content)
""")
    
    print("\n" + "="*80)
    print("VERIFICATION:")
    print("="*80)
    print(f"✓ Found {report.get('levels', {}).get('0', 0)} Components (expected: 3)")
    print(f"✓ Found {report.get('levels', {}).get('1', 0)} Level 1 topics (expected: ~18 main topics)")
    print(f"✓ Total: {report.get('topics_extracted', 0)} topics")
    print(f"\nTo verify completeness:")
    print("1. Check your database viewer - look for all 3 Components")
    print("2. Under Component 1, verify all 9 main topics are present")
    print("3. Under Component 2, verify all 9 main topics are present")
    print("4. Check that topics have real content (not placeholders)")
    print("\nIf Level 1 count is less than ~18, some main topics may be missing.")
else:
    print(f"Report file not found: {report_file}")





















