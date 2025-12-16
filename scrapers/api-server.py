"""
Paper Extraction API Server
Runs on Railway and provides extraction endpoints for the FLASH app
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys
import traceback
from datetime import datetime, timezone

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
      "extraction_status_id": "uuid",  (optional, but recommended)
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
        extraction_status_id = data.get('extraction_status_id')
        question_url = data.get('question_url')
        mark_scheme_url = data.get('mark_scheme_url')
        examiner_report_url = data.get('examiner_report_url')

        if not paper_id:
            return jsonify({'error': 'paper_id is required'}), 400

        # Supabase client (service role)
        from supabase import create_client
        sb = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))

        def update_status(patch: dict):
            """
            Update the background job status row if provided.
            We update by `id` to avoid legacy schema collisions and to support user-specific rows.
            """
            if not extraction_status_id:
                return
            sb.table('paper_extraction_status').update(patch).eq('id', extraction_status_id).execute()

        # Mark as extracting
        update_status({
            'status': 'extracting',
            'progress_percentage': 5,
            'current_step': 'Starting extraction...',
            'error_message': None,
            'started_at': datetime.now(timezone.utc).isoformat(),
        })
        
        result = {
            'paper_id': paper_id,
            'success': True,
            'extractions': {}
        }
        
        # Extract questions
        print(f"[INFO] Extracting questions from {question_url}")
        update_status({
            'status': 'extracting',
            'progress_percentage': 10,
            'current_step': 'Extracting questions...',
        })
        questions = extract_questions(question_url, paper_id)
        result['extractions']['questions'] = {
            'count': len(questions),
            'status': 'success'
        }
        update_status({
            'status': 'extracting',
            'progress_percentage': 70,
            'current_step': f'Questions extracted ({len(questions)})',
        })
        
        # Extract mark scheme if available
        if mark_scheme_url:
            print(f"[INFO] Extracting mark scheme from {mark_scheme_url}")
            update_status({
                'status': 'extracting',
                'progress_percentage': 75,
                'current_step': 'Extracting mark scheme...',
            })
            mark_schemes = extract_mark_scheme(mark_scheme_url, paper_id)
            result['extractions']['mark_schemes'] = {
                'count': len(mark_schemes),
                'status': 'success'
            }
            update_status({
                'status': 'extracting',
                'progress_percentage': 90,
                'current_step': f'Mark scheme processed ({len(mark_schemes)})',
            })
        
        # Mark completed
        update_status({
            'status': 'completed',
            'progress_percentage': 100,
            'current_step': 'Completed',
            'completed_at': datetime.now(timezone.utc).isoformat(),
        })
        
        return jsonify(result)
        
    except Exception as e:
        print(f"[ERROR] Extraction failed: {str(e)}")
        traceback.print_exc()

        # Best-effort: if we have an extraction status id, mark it failed
        try:
            data = request.json or {}
            extraction_status_id = data.get('extraction_status_id')
            if extraction_status_id:
                from supabase import create_client
                sb = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))
                sb.table('paper_extraction_status').update({
                    'status': 'failed',
                    'progress_percentage': 0,
                    'current_step': 'Failed',
                    'error_message': str(e),
                    'completed_at': datetime.now(timezone.utc).isoformat(),
                }).eq('id', extraction_status_id).execute()
        except Exception as _inner:
            print(f"[WARN] Failed to update extraction status row: {_inner}")

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
        time_taken_seconds = data.get('time_taken_seconds', 0)
        
        # Mark the answer
        marking = mark_answer(question_id, user_answer, user_id, time_taken_seconds)
        
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

