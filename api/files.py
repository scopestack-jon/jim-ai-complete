import os
import json
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

FILES_DB = 'files.json'

def load_files():
    """Load files from JSON storage"""
    if os.path.exists(FILES_DB):
        with open(FILES_DB, 'r') as f:
            return json.load(f)
    return []

@app.route('/api/files', methods=['GET'])
def list_files():
    """List all uploaded files"""
    try:
        files = load_files()
        # Sort by upload date, newest first
        files.sort(key=lambda x: x.get('upload_date', ''), reverse=True)
        return jsonify(files)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# For Vercel
def handler(request):
    return app(request.environ, lambda status, headers: None)

if __name__ == '__main__':
    app.run(debug=True, port=5000)

