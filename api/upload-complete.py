import os
import json
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Simple file-based storage for demo (replace with database in production)
FILES_DB = 'files.json'

def load_files():
    """Load files from JSON storage"""
    if os.path.exists(FILES_DB):
        with open(FILES_DB, 'r') as f:
            return json.load(f)
    return []

def save_files(files):
    """Save files to JSON storage"""
    with open(FILES_DB, 'w') as f:
        json.dump(files, f, indent=2)

@app.route('/api/upload-complete', methods=['POST'])
def upload_complete():
    """Mark upload as complete and store metadata"""
    try:
        data = request.json
        file_id = data.get('file_id')
        s3_key = data.get('s3_key')
        filename = data.get('filename')
        file_size = data.get('file_size')
        file_type = data.get('file_type')
        case_id = data.get('case_id')
        description = data.get('description')
        
        if not all([file_id, s3_key, filename]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Load existing files
        files = load_files()
        
        # Add new file record
        file_record = {
            'id': file_id,
            's3_key': s3_key,
            'filename': filename,
            'file_size': file_size,
            'file_type': file_type,
            'case_id': case_id,
            'description': description,
            'upload_date': datetime.now().isoformat(),
            'status': 'uploaded'
        }
        
        files.append(file_record)
        save_files(files)
        
        return jsonify({
            'success': True,
            'file_id': file_id,
            'status': 'uploaded'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# For Vercel
def handler(request):
    return app(request.environ, lambda status, headers: None)

if __name__ == '__main__':
    app.run(debug=True, port=5000)

