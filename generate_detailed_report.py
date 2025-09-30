#!/usr/bin/env python
"""
Generate Detailed Report of Scraped Data
Shows ACTUAL data scraped, not just success/failure
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

def generate_detailed_report():
    """Generate detailed HTML report showing actual scraped data."""
    
    # Connect to Supabase
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_KEY')
    
    if not url or not key:
        print("ERROR: Missing SUPABASE credentials")
        return 1
    
    client = create_client(url, key)
    
    print("Fetching data from Supabase...\n")
    
    # Get all AQA exam_board_subjects
    aqa_result = client.table('exam_boards').select('id').eq('code', 'AQA').execute()
    if not aqa_result.data:
        print("ERROR: AQA not found in exam_boards table")
        return 1
    
    aqa_id = aqa_result.data[0]['id']
    
    # Get all AQA subjects with topic counts
    subjects = client.table('exam_board_subjects').select('''
        id,
        subject_name,
        subject_code,
        qualification_type:qualification_types(code, name),
        created_at,
        updated_at
    ''').eq('exam_board_id', aqa_id).execute().data
    
    print(f"Found {len(subjects)} AQA subjects in database\n")
    
    # For each subject, get topic count and sample
    detailed_subjects = []
    
    for subject in subjects:
        # Count topics
        topic_count_result = client.table('curriculum_topics').select('id', count='exact').eq(
            'exam_board_subject_id', subject['id']
        ).execute()
        
        topic_count = topic_count_result.count or 0
        
        # Get sample topics
        sample_topics = client.table('curriculum_topics').select(
            'topic_code,topic_name,topic_level,chronological_period,geographical_region,key_themes'
        ).eq('exam_board_subject_id', subject['id']).limit(5).execute().data
        
        # Get latest update
        latest_topic = client.table('curriculum_topics').select('updated_at').eq(
            'exam_board_subject_id', subject['id']
        ).order('updated_at', desc=True).limit(1).execute().data
        
        last_scraped = latest_topic[0]['updated_at'] if latest_topic else None
        
        detailed_subjects.append({
            **subject,
            'topic_count': topic_count,
            'sample_topics': sample_topics,
            'last_scraped': last_scraped
        })
    
    # Sort by topic count (most topics first)
    detailed_subjects.sort(key=lambda x: x['topic_count'], reverse=True)
    
    # Generate HTML
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Detailed Scraping Report - {datetime.now().strftime('%Y-%m-%d')}</title>
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; margin: 20px; background: #f5f7fa; }}
        .container {{ max-width: 1600px; margin: 0 auto; background: white; padding: 40px; border-radius: 12px; }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 14px; }}
        th {{ background: #34495e; color: white; padding: 12px; text-align: left; position: sticky; top: 0; }}
        td {{ padding: 10px; border-bottom: 1px solid #ddd; vertical-align: top; }}
        tr:hover {{ background: #f8f9fa; }}
        .good {{ color: #27ae60; font-weight: bold; }}
        .warning {{ color: #f39c12; font-weight: bold; }}
        .bad {{ color: #e74c3c; font-weight: bold; }}
        .sample-topics {{ background: #f8f9fa; padding: 10px; border-radius: 4px; margin: 5px 0; }}
        .topic-item {{ margin: 3px 0; font-size: 12px; }}
        .code {{ background: #3498db; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px; }}
        .level {{ background: #95a5a6; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px; }}
        pre {{ background: #f4f4f4; padding: 15px; border-radius: 4px; overflow-x: auto; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Detailed AQA Scraping Report</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Total Subjects: <strong>{len(subjects)}</strong></p>
        
        <h2>Subjects with Topic Data</h2>
        <table>
            <tr>
                <th style="width: 30px;">#</th>
                <th>Subject</th>
                <th>Code</th>
                <th>Qualification</th>
                <th>Topics</th>
                <th>Last Updated</th>
                <th>Sample Topics</th>
            </tr>
"""
    
    for i, subj in enumerate(detailed_subjects, 1):
        topic_count = subj['topic_count']
        count_class = 'good' if topic_count > 10 else 'warning' if topic_count > 0 else 'bad'
        qual_code = subj.get('qualification_type', {}).get('code', 'N/A') if isinstance(subj.get('qualification_type'), dict) else 'N/A'
        
        # Format sample topics
        sample_html = '<div class="sample-topics">'
        for topic in subj['sample_topics']:
            code = topic.get('topic_code', 'N/A')
            name = topic.get('topic_name', 'N/A')
            level = topic.get('topic_level', '?')
            period = topic.get('chronological_period', '')
            region = topic.get('geographical_region', '')
            
            sample_html += f'<div class="topic-item">'
            sample_html += f'<span class="code">{code}</span> '
            sample_html += f'<span class="level">L{level}</span> '
            sample_html += f'{name[:80]}'
            if period:
                sample_html += f' <em>({period})</em>'
            if region:
                sample_html += f' [{region}]'
            sample_html += f'</div>'
        
        if not subj['sample_topics']:
            sample_html += '<em>No topics</em>'
        
        sample_html += '</div>'
        
        last_scraped = subj.get('last_scraped', '')
        if last_scraped:
            last_scraped = last_scraped[:10]  # Just date
        
        html += f'''
            <tr>
                <td>{i}</td>
                <td><strong>{subj['subject_name']}</strong></td>
                <td>{subj['subject_code']}</td>
                <td>{qual_code}</td>
                <td class="{count_class}">{topic_count}</td>
                <td>{last_scraped}</td>
                <td>{sample_html}</td>
            </tr>
'''
    
    html += """
        </table>
        
        <h2>SQL Queries for Investigation</h2>
        <pre>
-- Count topics by subject
SELECT 
  ebs.subject_name,
  COUNT(ct.id) as topic_count,
  MAX(ct.updated_at) as last_updated
FROM exam_board_subjects ebs
JOIN exam_boards eb ON ebs.exam_board_id = eb.id
LEFT JOIN curriculum_topics ct ON ct.exam_board_subject_id = ebs.id
WHERE eb.code = 'AQA'
GROUP BY ebs.subject_name
ORDER BY topic_count DESC;

-- See today's scraped topics
SELECT 
  ct.topic_code,
  ct.topic_name,
  ct.topic_level,
  ebs.subject_name,
  ct.created_at
FROM curriculum_topics ct
JOIN exam_board_subjects ebs ON ct.exam_board_subject_id = ebs.id
JOIN exam_boards eb ON ebs.exam_board_id = eb.id
WHERE eb.code = 'AQA'
AND DATE(ct.created_at) = CURRENT_DATE
ORDER BY ebs.subject_name, ct.topic_code;
        </pre>
    </div>
</body>
</html>"""
    
    # Save report
    report_file = f'data/reports/detailed_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html'
    Path(report_file).parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"\nDetailed report generated: {report_file}")
    
    # Open in browser
    import webbrowser
    webbrowser.open(f'file:///{Path(report_file).absolute()}')
    
    return 0

if __name__ == '__main__':
    sys.exit(generate_detailed_report())
