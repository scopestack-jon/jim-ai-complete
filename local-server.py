#!/usr/bin/env python3
"""
Local development server for JIM AI
Runs all API endpoints on localhost:5000 for testing
"""

import os
import sys
from flask import Flask, request
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Import all API endpoints
sys.path.append('api')

from config import get_config
from files import list_files

# Import the individual endpoint functions
import importlib.util

def load_module_from_file(filepath, module_name):
    """Load a Python module from file path"""
    spec = importlib.util.spec_from_file_location(module_name, filepath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Load upload endpoints
upload_url_module = load_module_from_file('api/upload-url.py', 'upload_url')
upload_complete_module = load_module_from_file('api/upload-complete.py', 'upload_complete')
multipart_module = load_module_from_file('api/multipart-upload.py', 'multipart_upload')
file_ops_module = load_module_from_file('api/files/[id].py', 'file_ops')
download_module = load_module_from_file('api/download-url/[id].py', 'download_url')

# Register routes
@app.route('/api/config', methods=['GET'])
def config():
    return get_config()

@app.route('/api/files', methods=['GET'])
def files():
    return list_files()

@app.route('/api/upload-url', methods=['POST'])
def upload_url():
    return upload_url_module.generate_upload_url()

@app.route('/api/upload-complete', methods=['POST'])
def upload_complete():
    return upload_complete_module.upload_complete()

# Multipart upload endpoints
@app.route('/api/multipart-upload/initiate', methods=['POST'])
def initiate_multipart():
    return multipart_module.initiate_multipart_upload()

@app.route('/api/multipart-upload/chunk', methods=['POST'])
def get_chunk_url():
    return multipart_module.get_chunk_upload_url()

@app.route('/api/multipart-upload/complete', methods=['POST'])
def complete_multipart():
    return multipart_module.complete_multipart_upload()

@app.route('/api/multipart-upload/abort', methods=['POST'])
def abort_multipart():
    return multipart_module.abort_multipart_upload()

@app.route('/api/files/<file_id>', methods=['GET', 'DELETE'])
def file_operations(file_id):
    if request.method == 'GET':
        return file_ops_module.get_file(file_id)
    elif request.method == 'DELETE':
        return file_ops_module.delete_file(file_id)

@app.route('/api/files/<file_id>/download-url', methods=['GET'])
def download_url(file_id):
    return download_module.generate_download_url(file_id)

@app.route('/health')
def health():
    return {'status': 'healthy', 'service': 'JIM AI API'}

if __name__ == '__main__':
    # Check environment variables
    required_vars = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'S3_BUCKET_NAME']
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease create a .env file with your AWS credentials.")
        print("See .env.example for the required format.")
        sys.exit(1)
    
    print("🚀 Starting JIM AI local development server...")
    print(f"📁 S3 Bucket: {os.environ.get('S3_BUCKET_NAME')}")
    print(f"🌍 AWS Region: {os.environ.get('AWS_REGION', 'us-east-1')}")
    print("🔗 API will be available at: http://localhost:5001")
    print("🔗 Frontend should run at: http://localhost:5173")
    print("\nPress Ctrl+C to stop the server")
    
    app.run(host='0.0.0.0', port=5001, debug=True)

