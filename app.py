#!/usr/bin/env python3
"""
JIM AI - Local Forensic Chat Interface
Flask web app for chatting with Bedrock Knowledge Base
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import boto3
import json
import time
from datetime import datetime
import os
import hashlib
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

app = Flask(__name__)
app.secret_key = 'jim-ai-forensic-app-secret-key'

# Configuration
KB_ID = "HFCMSKWHFU"
MODEL_ARN = "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-5-sonnet-20240620-v1:0"
REGION = "us-east-1"
S3_BUCKET = "jim-ai-forensic-data-1758988022"
UPLOAD_FOLDER = "/tmp/claude"
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB max file size for web upload
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx', 'csv', 'json', 'html', 'xml', 'db', 'sqlite', 'zip', 'tar', 'gz'}

# Create upload directory
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize AWS clients
bedrock_client = boto3.client('bedrock-agent-runtime', region_name=REGION)
s3_client = boto3.client('s3', region_name=REGION)
bedrock_agent_client = boto3.client('bedrock-agent', region_name=REGION)

class ChatHistory:
    def __init__(self):
        self.messages = []

    def add_message(self, role, content, sources=None):
        self.messages.append({
            'role': role,
            'content': content,
            'sources': sources or [],
            'timestamp': datetime.now().strftime('%H:%M:%S')
        })

    def get_messages(self):
        return self.messages

# Global chat history
chat_history = ChatHistory()

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def calculate_checksum(file_path):
    """Calculate SHA256 checksum of file"""
    hash_sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()

def upload_to_s3(file_path, s3_key):
    """Upload file to S3 bucket"""
    try:
        s3_client.upload_file(file_path, S3_BUCKET, s3_key)
        return True
    except Exception as e:
        print(f"Error uploading to S3: {str(e)}")
        return False

def split_large_file(file_path, max_size_mb=50):
    """Split large files into smaller chunks"""
    max_size_bytes = max_size_mb * 1024 * 1024
    file_size = os.path.getsize(file_path)

    if file_size <= max_size_bytes:
        return [file_path]

    chunks = []
    filename = os.path.basename(file_path)
    name, ext = os.path.splitext(filename)

    with open(file_path, 'rb') as f:
        chunk_num = 1
        while True:
            chunk_data = f.read(max_size_bytes)
            if not chunk_data:
                break

            chunk_filename = f"{name}_part{chunk_num:03d}{ext}"
            chunk_path = os.path.join(UPLOAD_FOLDER, chunk_filename)

            with open(chunk_path, 'wb') as chunk_file:
                chunk_file.write(chunk_data)

            chunks.append(chunk_path)
            chunk_num += 1

    return chunks

def start_ingestion_job():
    """Start Bedrock Knowledge Base ingestion job"""
    try:
        response = bedrock_agent_client.start_ingestion_job(
            knowledgeBaseId=KB_ID,
            dataSourceId="CZJWLDWEFD"
        )
        return response['ingestionJob']['ingestionJobId']
    except Exception as e:
        print(f"Error starting ingestion job: {str(e)}")
        return None

@app.route('/')
def index():
    """Main chat interface"""
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages"""
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()

        if not user_message:
            return jsonify({'error': 'Empty message'}), 400

        # Add user message to history
        chat_history.add_message('user', user_message)

        # Add typing delay to prevent rate limiting
        time.sleep(1)

        # Query Bedrock Knowledge Base
        response = bedrock_client.retrieve_and_generate(
            input={'text': user_message},
            retrieveAndGenerateConfiguration={
                'type': 'KNOWLEDGE_BASE',
                'knowledgeBaseConfiguration': {
                    'knowledgeBaseId': KB_ID,
                    'modelArn': MODEL_ARN
                }
            }
        )

        # Extract answer and sources
        answer = response['output']['text']
        citations = response.get('citations', [])

        # Format sources
        sources = []
        for citation in citations:
            for ref in citation.get('retrievedReferences', []):
                location = ref.get('location', {}).get('s3Location', {})
                uri = location.get('uri', 'Unknown')
                # Extract filename from S3 URI
                filename = uri.split('/')[-1] if '/' in uri else uri
                sources.append({
                    'filename': filename,
                    'uri': uri
                })

        # Add assistant response to history
        chat_history.add_message('assistant', answer, sources)

        return jsonify({
            'answer': answer,
            'sources': sources,
            'timestamp': datetime.now().strftime('%H:%M:%S')
        })

    except Exception as e:
        error_msg = f"Error: {str(e)}"
        chat_history.add_message('assistant', error_msg)
        return jsonify({'error': error_msg}), 500

@app.route('/api/history')
def get_history():
    """Get chat history"""
    return jsonify(chat_history.get_messages())

@app.route('/api/clear')
def clear_history():
    """Clear chat history"""
    global chat_history
    chat_history = ChatHistory()
    return jsonify({'status': 'cleared'})

@app.route('/api/upload', methods=['POST'])
def upload_files():
    """Handle file uploads"""
    try:
        if 'files' not in request.files:
            return jsonify({'error': 'No files selected'}), 400

        files = request.files.getlist('files')
        if not files or all(f.filename == '' for f in files):
            return jsonify({'error': 'No files selected'}), 400

        uploaded_files = []
        total_size = 0

        for file in files:
            if file and file.filename != '':
                if not allowed_file(file.filename):
                    return jsonify({'error': f'File type not allowed: {file.filename}'}), 400

                # Check file size
                file.seek(0, 2)  # Seek to end
                file_size = file.tell()
                file.seek(0)  # Reset to beginning

                if file_size > MAX_FILE_SIZE:
                    return jsonify({'error': f'File too large: {file.filename} ({file_size/1024/1024:.1f}MB > 100MB). Use the large-data-processor.py script for files >100MB.'}), 400

                total_size += file_size

        if total_size > MAX_FILE_SIZE * 5:  # Max 500MB total per upload
            return jsonify({'error': f'Total upload size too large ({total_size/1024/1024:.1f}MB > 500MB)'}), 400

        # Process each file
        for file in files:
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                unique_filename = f"{timestamp}_{filename}"
                file_path = os.path.join(UPLOAD_FOLDER, unique_filename)

                # Save file
                file.save(file_path)

                # Calculate checksum
                checksum = calculate_checksum(file_path)

                # Split if too large for Knowledge Base
                file_chunks = split_large_file(file_path)

                # Upload to S3
                for chunk_path in file_chunks:
                    chunk_filename = os.path.basename(chunk_path)
                    s3_key = f"kb/{chunk_filename}"

                    if upload_to_s3(chunk_path, s3_key):
                        uploaded_files.append({
                            'original_name': filename,
                            'uploaded_name': chunk_filename,
                            's3_key': s3_key,
                            'size': os.path.getsize(chunk_path),
                            'checksum': calculate_checksum(chunk_path)
                        })

                    # Clean up chunk file if it's different from original
                    if chunk_path != file_path:
                        os.remove(chunk_path)

                # Clean up original file
                os.remove(file_path)

        # Start ingestion job
        job_id = start_ingestion_job()

        return jsonify({
            'success': True,
            'files_uploaded': len(uploaded_files),
            'files': uploaded_files,
            'ingestion_job_id': job_id,
            'message': f'Successfully uploaded {len(uploaded_files)} files. Ingestion job started.'
        })

    except Exception as e:
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@app.route('/api/ingestion-status')
def ingestion_status():
    """Get latest ingestion job status"""
    try:
        response = bedrock_agent_client.list_ingestion_jobs(
            knowledgeBaseId=KB_ID,
            dataSourceId="CZJWLDWEFD",
            maxResults=1
        )

        if response['ingestionJobSummaries']:
            latest_job = response['ingestionJobSummaries'][0]
            return jsonify({
                'job_id': latest_job['ingestionJobId'],
                'status': latest_job['status'],
                'started_at': latest_job['startedAt'].isoformat(),
                'updated_at': latest_job['updatedAt'].isoformat() if 'updatedAt' in latest_job else None
            })
        else:
            return jsonify({'status': 'NO_JOBS'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/status')
def status():
    """Get system status"""
    return jsonify({
        'knowledge_base_id': KB_ID,
        'model': MODEL_ARN.split('/')[-1],
        'region': REGION,
        's3_bucket': S3_BUCKET,
        'status': 'online'
    })

if __name__ == '__main__':
    print("🚀 Starting JIM AI Forensic Chat Interface...")
    print(f"📊 Knowledge Base: {KB_ID}")
    print(f"🤖 Model: {MODEL_ARN.split('/')[-1]}")
    print(f"🌍 Region: {REGION}")
    print("💻 Open your browser to: http://localhost:8080")
    print("=" * 50)

    app.run(debug=True, host='0.0.0.0', port=8080)