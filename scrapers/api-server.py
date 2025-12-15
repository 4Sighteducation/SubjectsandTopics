"""
Paper Extraction API Server
Runs on Railway and provides extraction endpoints for the FLASH app
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys

# Import our test scripts as modules
sys.path.append(os.path.dirname(__file__))

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
def extract_paper():
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
        
        # TODO: Import and call the actual extraction functions
        # For now, return mock response
        result['extractions']['questions'] = {
            'status': 'pending',
            'message': 'Extraction service is being set up'
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

