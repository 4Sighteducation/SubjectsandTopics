"""
Paper Extraction API Server
Runs on Railway and provides extraction endpoints for the FLASH app
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys
import traceback

# Import extraction service
sys.path.append(os.path.dirname(__file__))
from extraction_service import extract_questions, extract_mark_scheme, mark_answer

app = Flask(__name__)
CORS(app)  # Allow requests from React Native app

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'service': 'FLASH Paper Extraction API',
        'status': 'running',
        'version': '1.0.0',
        'endpoints': [
            'POST /api/extract-paper',
            'GET /health'
        ]
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'})

@app.route('/api/extract-paper', methods=['POST'])
def extract_paper_endpoint():
    """
    Extract questions, mark scheme, and examiner insights from a paper
    
    Request body:
    {
      "paper_id": "uuid",
      "question_url": "https://...",
      "mark_scheme_url": "https://...",  (optional)
      "examiner_report_url": "https://..."  (optional)
    }
    """
    try:
        data = request.json
        
        if not data or not data.get('question_url'):
            return jsonify({'error': 'question_url is required'}), 400
        
        paper_id = data.get('paper_id')
        question_url = data.get('question_url')
        mark_scheme_url = data.get('mark_scheme_url')
        examiner_report_url = data.get('examiner_report_url')
        
        result = {
            'paper_id': paper_id,
            'success': True,
            'extractions': {}
        }
        
        # Extract questions
        print(f"[INFO] Extracting questions from {question_url}")
        questions = extract_questions(question_url, paper_id)
        result['extractions']['questions'] = {
            'count': len(questions),
            'status': 'success'
        }
        
        # Extract mark scheme if available
        if mark_scheme_url:
            print(f"[INFO] Extracting mark scheme from {mark_scheme_url}")
            mark_schemes = extract_mark_scheme(mark_scheme_url, paper_id)
            result['extractions']['mark_schemes'] = {
                'count': len(mark_schemes),
                'status': 'success'
            }
        
        # Update extraction status
        from supabase import create_client
        sb = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))
        sb.table('paper_extraction_status').upsert({
            'paper_id': paper_id,
            'questions_extracted': True,
            'mark_scheme_extracted': bool(mark_scheme_url),
            'questions_count': len(questions),
        }).execute()
        
        return jsonify(result)
        
    except Exception as e:
        print(f"[ERROR] Extraction failed: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.route('/api/mark-answer', methods=['POST'])
def mark_answer_endpoint():
    """
    Mark a student's answer using AI + mark scheme
    
    Request body:
    {
      "question_id": "uuid",
      "user_answer": "text",
      "user_id": "uuid"
    }
    """
    try:
        data = request.json
        
        if not data or not data.get('question_id') or not data.get('user_answer'):
            return jsonify({'error': 'question_id and user_answer are required'}), 400
        
        question_id = data.get('question_id')
        user_answer = data.get('user_answer')
        user_id = data.get('user_id')
        
        # Mark the answer
        marking = mark_answer(question_id, user_answer, user_id)
        
        return jsonify({
            'success': True,
            'marking': marking
        })
        
    except Exception as e:
        print(f"[ERROR] Marking failed: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

