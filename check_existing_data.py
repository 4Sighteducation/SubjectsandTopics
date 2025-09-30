#!/usr/bin/env python
"""
Check Existing Data in Supabase
Investigate what curriculum data already exists and what's missing
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client
from datetime import datetime

load_dotenv()

def create_html_report(data: dict, filename: str):
    """Generate HTML report."""
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Supabase Data Audit - {datetime.now().strftime('%Y-%m-%d')}</title>
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; margin: 20px; background: #f5f7fa; }}
        .container {{ max-width: 1400px; margin: 0 auto; background: white; padding: 40px; border-radius: 12px; }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; border-left: 4px solid #3498db; padding-left: 15px; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 20px 0; }}
        .stat-card {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 25px; border-radius: 8px; color: white; text-align: center; }}
        .stat-card.green {{ background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); }}
        .stat-card.red {{ background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%); }}
        .stat-card.yellow {{ background: linear-gradient(135deg, #f2994a 0%, #f2c94c 100%); }}
        .stat-number {{ font-size: 48px; font-weight: bold; }}
        .stat-label {{ font-size: 14px; opacity: 0.9; margin-top: 5px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th {{ background: #34495e; color: white; padding: 12px; text-align: left; }}
        td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
        tr:hover {{ background: #f8f9fa; }}
        .empty {{ color: #e74c3c; font-weight: bold; }}
        .filled {{ color: #27ae60; font-weight: bold; }}
        .badge {{ display: inline-block; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: bold; }}
        .badge.success {{ background: #38ef7d; color: white; }}
        .badge.warning {{ background: #f2c94c; color: #333; }}
        .badge.danger {{ background: #f45c43; color: white; }}
        .section {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 FLASH Database Audit Report</h1>
        <p style="color: #7f8c8d;">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <h2>Core Data Status</h2>
        <div class="grid">
            <div class="stat-card green">
                <div class="stat-number">{data['exam_boards']}</div>
                <div class="stat-label">Exam Boards</div>
            </div>
            <div class="stat-card green">
                <div class="stat-number">{data['qualification_types']}</div>
                <div class="stat-label">Qualification Types</div>
            </div>
            <div class="stat-card {'green' if data['exam_board_subjects'] > 0 else 'red'}">
                <div class="stat-number">{data['exam_board_subjects']}</div>
                <div class="stat-label">Subjects</div>
            </div>
            <div class="stat-card {'green' if data['curriculum_topics'] > 0 else 'red'}">
                <div class="stat-number">{data['curriculum_topics']:,}</div>
                <div class="stat-label">Topics</div>
            </div>
        </div>
        
        <h2>Specification Tables (Enhanced Data)</h2>
        <div class="grid">
            <div class="stat-card {'green' if data['specification_metadata'] > 0 else 'red'}">
                <div class="stat-number">{data['specification_metadata']}</div>
                <div class="stat-label">Specifications</div>
            </div>
            <div class="stat-card {'yellow' if data['spec_components'] > 0 else 'red'}">
                <div class="stat-number">{data['spec_components']}</div>
                <div class="stat-label">Components</div>
            </div>
            <div class="stat-card {'yellow' if data['selection_constraints'] > 0 else 'red'}">
                <div class="stat-number">{data['selection_constraints']}</div>
                <div class="stat-label">Constraints</div>
            </div>
            <div class="stat-card {'yellow' if data['subject_vocabulary'] > 0 else 'red'}">
                <div class="stat-number">{data['subject_vocabulary']}</div>
                <div class="stat-label">Vocabulary Terms</div>
            </div>
        </div>
        
        <h2>Assessment Resources Tables</h2>
        <div class="grid">
            <div class="stat-card {'green' if data['exam_papers'] > 0 else 'red'}">
                <div class="stat-number">{data['exam_papers']}</div>
                <div class="stat-label">Exam Papers</div>
            </div>
            <div class="stat-card {'yellow' if data['mark_scheme_insights'] > 0 else 'red'}">
                <div class="stat-number">{data['mark_scheme_insights']}</div>
                <div class="stat-label">Mark Scheme Insights</div>
            </div>
            <div class="stat-card {'yellow' if data['examiner_report_insights'] > 0 else 'red'}">
                <div class="stat-number">{data['examiner_report_insights']}</div>
                <div class="stat-label">Examiner Reports</div>
            </div>
            <div class="stat-card {'yellow' if data['question_bank'] > 0 else 'red'}">
                <div class="stat-number">{data['question_bank']}</div>
                <div class="stat-label">Questions</div>
            </div>
        </div>
        
        <div class="section">
            <h2>📋 Sample Data</h2>
            
            <h3>Exam Boards</h3>
            <table>
                <tr><th>Code</th><th>Name</th><th>Country</th></tr>
                {generate_table_rows(data.get('exam_boards_sample', []), ['code', 'full_name', 'country'])}
            </table>
            
            <h3>Subjects (Sample)</h3>
            <table>
                <tr><th>Board</th><th>Qualification</th><th>Subject</th><th>Code</th><th>Topics</th></tr>
                {generate_subjects_table(data.get('subjects_sample', []))}
            </table>
            
            <h3>Specification Metadata (if any)</h3>
            <table>
                <tr><th>Board</th><th>Qualification</th><th>Subject</th><th>Components</th><th>Constraints</th></tr>
                {generate_specs_table(data.get('specifications_sample', []))}
            </table>
        </div>
        
        <div class="section">
            <h2>🔍 Data Quality Analysis</h2>
            <h3>Topics by Exam Board</h3>
            <table>
                <tr><th>Exam Board</th><th>Topic Count</th><th>Status</th></tr>
                {generate_board_stats(data.get('topics_by_board', []))}
            </table>
            
            <h3>Topics by Level</h3>
            <table>
                <tr><th>Level</th><th>Count</th><th>Description</th></tr>
                {generate_level_stats(data.get('topics_by_level', []))}
            </table>
        </div>
        
        <div class="section">
            <h2>✅ Recommendations</h2>
            <ul>
{generate_recommendations(data)}
            </ul>
        </div>
    </div>
</body>
</html>"""
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"\n✅ Report generated: {filename}")
    
    # Open in browser
    import webbrowser
    webbrowser.open(f'file:///{Path(filename).absolute()}')

def generate_table_rows(rows, cols):
    if not rows:
        return '<tr><td colspan="3" class="empty">No data</td></tr>'
    html = ''
    for row in rows[:10]:  # Limit to 10 rows
        html += '<tr>'
        for col in cols:
            html += f'<td>{row.get(col, "")}</td>'
        html += '</tr>\n'
    return html

def generate_subjects_table(subjects):
    if not subjects:
        return '<tr><td colspan="5" class="empty">No subjects</td></tr>'
    html = ''
    for s in subjects[:20]:
        board_code = s.get('exam_board', {}).get('code', 'N/A') if isinstance(s.get('exam_board'), dict) else 'N/A'
        qual_code = s.get('qualification_type', {}).get('code', 'N/A') if isinstance(s.get('qualification_type'), dict) else 'N/A'
        topic_count = s.get('topic_count', 0)
        status = 'filled' if topic_count > 0 else 'empty'
        html += f'<tr><td>{board_code}</td><td>{qual_code}</td><td>{s.get("subject_name", "")}</td><td>{s.get("subject_code", "")}</td><td class="{status}">{topic_count}</td></tr>\n'
    return html

def generate_specs_table(specs):
    if not specs:
        return '<tr><td colspan="5" class="empty">No specification metadata</td></tr>'
    html = ''
    for spec in specs:
        html += f'<tr><td>{spec.get("exam_board", "")}</td><td>{spec.get("qualification_type", "")}</td><td>{spec.get("subject_name", "")}</td><td class="filled">{spec.get("components_count", 0)}</td><td class="filled">{spec.get("constraints_count", 0)}</td></tr>\n'
    return html

def generate_board_stats(stats):
    if not stats:
        return '<tr><td colspan="3" class="empty">No data</td></tr>'
    html = ''
    for stat in stats:
        count = stat.get('count', 0)
        status = 'filled' if count > 100 else 'empty' if count == 0 else 'warning'
        badge = 'success' if count > 100 else 'danger' if count == 0 else 'warning'
        html += f'<tr><td>{stat.get("board", "Unknown")}</td><td class="{status}">{count:,}</td><td><span class="badge {badge}">{"Good" if count > 100 else "Empty" if count == 0 else "Sparse"}</span></td></tr>\n'
    return html

def generate_level_stats(stats):
    if not stats:
        return '<tr><td colspan="3" class="empty">No data</td></tr>'
    html = ''
    level_names = {0: 'Options/Modules', 1: 'Topics', 2: 'Subtopics'}
    for stat in stats:
        level = stat.get('topic_level', -1)
        html += f'<tr><td>{level}</td><td class="filled">{stat.get("count", 0):,}</td><td>{level_names.get(level, "Unknown")}</td></tr>\n'
    return html

def generate_recommendations(data):
    recs = []
    
    if data['specification_metadata'] == 0:
        recs.append('<li class="empty">❌ <strong>No specification metadata</strong> - Run batch_processor.py to scrape AQA subjects</li>')
    elif data['specification_metadata'] < 10:
        recs.append(f'<li class="warning">⚠️ <strong>Only {data["specification_metadata"]} specifications</strong> - Continue scraping more subjects</li>')
    else:
        recs.append('<li class="filled">✅ Specification metadata looks good!</li>')
    
    if data['exam_papers'] == 0:
        recs.append('<li class="empty">❌ <strong>No exam papers</strong> - Need to create assessment resources scraper</li>')
    
    if data['curriculum_topics'] == 0:
        recs.append('<li class="empty">❌ <strong>No curriculum topics</strong> - Need to import base topic data</li>')
    elif data['curriculum_topics'] < 1000:
        recs.append(f'<li class="warning">⚠️ <strong>Only {data["curriculum_topics"]} topics</strong> - May need more comprehensive scraping</li>')
    else:
        recs.append(f'<li class="filled">✅ Good topic coverage: {data["curriculum_topics"]:,} topics</li>')
    
    if data['selection_constraints'] > 0:
        recs.append(f'<li class="filled">✅ Selection constraints exist ({data["selection_constraints"]}) - Can implement pathway UI</li>')
    
    return '\n'.join(recs)


def main():
    """Check all tables and generate report."""
    print("=" * 60)
    print("SUPABASE DATA AUDIT")
    print("=" * 60)
    
    # Connect to Supabase
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_KEY')
    
    if not url or not key:
        print("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_KEY")
        return 1
    
    client = create_client(url, key)
    
    print("\n📊 Checking tables...\n")
    
    data = {}
    
    # Core tables
    print("Core Tables:")
    data['exam_boards'] = client.table('exam_boards').select('*', count='exact').execute().count or 0
    print(f"  - exam_boards: {data['exam_boards']}")
    
    data['qualification_types'] = client.table('qualification_types').select('*', count='exact').execute().count or 0
    print(f"  - qualification_types: {data['qualification_types']}")
    
    data['exam_board_subjects'] = client.table('exam_board_subjects').select('*', count='exact').execute().count or 0
    print(f"  - exam_board_subjects: {data['exam_board_subjects']}")
    
    data['curriculum_topics'] = client.table('curriculum_topics').select('*', count='exact').execute().count or 0
    print(f"  - curriculum_topics: {data['curriculum_topics']:,}")
    
    # Specification tables
    print("\nSpecification Tables:")
    data['specification_metadata'] = client.table('specification_metadata').select('*', count='exact').execute().count or 0
    print(f"  - specification_metadata: {data['specification_metadata']}")
    
    data['spec_components'] = client.table('spec_components').select('*', count='exact').execute().count or 0
    print(f"  - spec_components: {data['spec_components']}")
    
    data['selection_constraints'] = client.table('selection_constraints').select('*', count='exact').execute().count or 0
    print(f"  - selection_constraints: {data['selection_constraints']}")
    
    data['subject_vocabulary'] = client.table('subject_vocabulary').select('*', count='exact').execute().count or 0
    print(f"  - subject_vocabulary: {data['subject_vocabulary']}")
    
    # Assessment tables
    print("\nAssessment Resources Tables:")
    data['exam_papers'] = client.table('exam_papers').select('*', count='exact').execute().count or 0
    print(f"  - exam_papers: {data['exam_papers']}")
    
    data['mark_scheme_insights'] = client.table('mark_scheme_insights').select('*', count='exact').execute().count or 0
    print(f"  - mark_scheme_insights: {data['mark_scheme_insights']}")
    
    data['examiner_report_insights'] = client.table('examiner_report_insights').select('*', count='exact').execute().count or 0
    print(f"  - examiner_report_insights: {data['examiner_report_insights']}")
    
    data['question_bank'] = client.table('question_bank').select('*', count='exact').execute().count or 0
    print(f"  - question_bank: {data['question_bank']}")
    
    # Sample data
    print("\n📋 Fetching sample data...")
    data['exam_boards_sample'] = client.table('exam_boards').select('code,full_name,country').limit(10).execute().data
    
    data['subjects_sample'] = client.table('exam_board_subjects').select(
        'subject_name,subject_code,exam_board:exam_boards(code,full_name),qualification_type:qualification_types(code,name)'
    ).limit(20).execute().data
    
    # Count topics per subject
    for subject in data['subjects_sample']:
        topic_count = client.table('curriculum_topics').select('id', count='exact').eq(
            'exam_board_subject_id', subject['id']
        ).execute().count or 0
        subject['topic_count'] = topic_count
    
    # Get specification samples
    data['specifications_sample'] = client.table('specification_metadata').select('*').limit(10).execute().data
    for spec in data['specifications_sample']:
        components_count = client.table('spec_components').select('id', count='exact').eq(
            'spec_metadata_id', spec['id']
        ).execute().count or 0
        constraints_count = client.table('selection_constraints').select('id', count='exact').eq(
            'spec_metadata_id', spec['id']
        ).execute().count or 0
        spec['components_count'] = components_count
        spec['constraints_count'] = constraints_count
    
    # Statistics
    print("\n📊 Analyzing data quality...")
    
    # Topics by board - need to do this carefully
    # First get all topics with their exam_board_subject
    topics_with_board = client.table('curriculum_topics').select(
        'id,exam_board_subject_id,exam_board_subjects!inner(exam_board:exam_boards(code))'
    ).limit(10000).execute().data  # Adjust limit as needed
    
    # Count by board
    from collections import Counter
    board_counts = Counter()
    for topic in topics_with_board:
        try:
            board_code = topic.get('exam_board_subjects', {}).get('exam_board', {}).get('code', 'Unknown')
            board_counts[board_code] += 1
        except:
            pass
    
    data['topics_by_board'] = [{'board': board, 'count': count} for board, count in board_counts.items()]
    
    # Topics by level
    level_result = client.table('curriculum_topics').select('topic_level').execute().data
    level_counts = Counter(t.get('topic_level', -1) for t in level_result)
    data['topics_by_level'] = [{'topic_level': level, 'count': count} for level, count in sorted(level_counts.items())]
    
    # Generate report
    report_file = f'data/reports/data_audit_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html'
    Path(report_file).parent.mkdir(parents=True, exist_ok=True)
    create_html_report(data, report_file)
    
    print("\n" + "=" * 60)
    print("AUDIT COMPLETE")
    print("=" * 60)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
