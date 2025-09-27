#!/usr/bin/env python3
"""
Simplified JIM AI - Direct S3 Evidence Management
No Knowledge Base required - just S3 + Claude
"""

from flask import Flask, render_template, request, jsonify, send_file
import boto3
import os
from datetime import datetime
import json
from werkzeug.utils import secure_filename
import io

app = Flask(__name__)
app.secret_key = 'jim-ai-simple-forensic-key'

# Simple configuration
S3_BUCKET = "jim-ai-forensic-data-1758988022"  # Or create a new one
REGION = "us-east-1"

# AWS clients
s3_client = boto3.client('s3', region_name=REGION)
bedrock_client = boto3.client('bedrock-runtime', region_name=REGION)

class ForensicDataManager:
    """Manage forensic evidence in S3 with case-based structure"""

    def __init__(self):
        self.bucket = S3_BUCKET

    def list_cases(self):
        """List all case folders"""
        try:
            response = s3_client.list_objects_v2(
                Bucket=self.bucket,
                Prefix='',
                Delimiter='/'
            )

            cases = []
            for prefix in response.get('CommonPrefixes', []):
                case_name = prefix['Prefix'].rstrip('/')
                if case_name.startswith('Case-'):
                    cases.append(case_name)

            return sorted(cases)
        except Exception as e:
            print(f"Error listing cases: {e}")
            return []

    def list_case_contents(self, case_id):
        """List all files in a case"""
        try:
            response = s3_client.list_objects_v2(
                Bucket=self.bucket,
                Prefix=f"{case_id}/"
            )

            files = []
            for obj in response.get('Contents', []):
                files.append({
                    'key': obj['Key'],
                    'name': obj['Key'].split('/')[-1],
                    'category': obj['Key'].split('/')[1] if len(obj['Key'].split('/')) > 1 else 'Root',
                    'size': obj['Size'],
                    'modified': obj['LastModified'].isoformat()
                })

            return files
        except Exception as e:
            print(f"Error listing case contents: {e}")
            return []

    def upload_evidence(self, case_id, category, file_obj, filename):
        """Upload evidence to appropriate case folder"""
        try:
            # Create S3 key with case/category structure
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_filename = secure_filename(filename)
            s3_key = f"{case_id}/{category}/{timestamp}_{safe_filename}"

            # Upload to S3
            s3_client.upload_fileobj(file_obj, self.bucket, s3_key)

            return {
                'success': True,
                'key': s3_key,
                'url': f"s3://{self.bucket}/{s3_key}"
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_file_content(self, s3_key):
        """Retrieve file content from S3"""
        try:
            response = s3_client.get_object(Bucket=self.bucket, Key=s3_key)
            content = response['Body'].read()

            # Convert content based on file type
            if s3_key.endswith('.txt') or s3_key.endswith('.csv'):
                return content.decode('utf-8')
            elif s3_key.endswith('.json'):
                return json.loads(content)
            else:
                return f"[Binary file: {len(content)} bytes]"
        except Exception as e:
            return f"Error reading file: {e}"

    def search_case_with_claude(self, case_id, query):
        """Search case files using Claude directly"""
        try:
            # Get all text-based files from the case
            files = self.list_case_contents(case_id)

            # Collect relevant content
            context = f"Case {case_id} Evidence:\n\n"

            for file_info in files[:10]:  # Limit to first 10 files for context
                if any(file_info['name'].endswith(ext) for ext in ['.txt', '.csv', '.json', '.log']):
                    content = self.get_file_content(file_info['key'])
                    if isinstance(content, str) and len(content) < 5000:  # Limit size
                        context += f"File: {file_info['name']}\n"
                        context += f"Content: {content[:2000]}...\n\n"

            # Query Claude directly
            prompt = f"""You are a forensic analyst assistant. Based on the following evidence from {case_id},
            please answer this query: {query}

            {context}

            Provide a clear, concise answer based only on the evidence provided."""

            response = bedrock_client.invoke_model(
                modelId='anthropic.claude-3-5-sonnet-20240620-v1:0',
                contentType='application/json',
                accept='application/json',
                body=json.dumps({
                    'anthropic_version': 'bedrock-2023-05-31',
                    'max_tokens': 1000,
                    'messages': [{
                        'role': 'user',
                        'content': prompt
                    }]
                })
            )

            result = json.loads(response['body'].read())
            answer = result['content'][0]['text']

            return {
                'answer': answer,
                'files_searched': len(files),
                'case': case_id
            }

        except Exception as e:
            return {'error': str(e)}

# Initialize manager
manager = ForensicDataManager()

@app.route('/')
def index():
    """Main interface"""
    return render_template('simple_interface.html')

@app.route('/api/cases')
def get_cases():
    """Get list of all cases"""
    cases = manager.list_cases()
    return jsonify(cases)

@app.route('/api/case/<case_id>')
def get_case_contents(case_id):
    """Get contents of a specific case"""
    files = manager.list_case_contents(case_id)
    return jsonify(files)

@app.route('/api/upload', methods=['POST'])
def upload_evidence():
    """Upload evidence to a case"""
    case_id = request.form.get('case_id', 'Case-001')
    category = request.form.get('category', 'Documents')

    uploaded_files = []
    for file in request.files.getlist('files'):
        if file:
            result = manager.upload_evidence(
                case_id,
                category,
                file,
                file.filename
            )
            uploaded_files.append(result)

    return jsonify({
        'uploaded': uploaded_files,
        'case': case_id,
        'category': category
    })

@app.route('/api/search', methods=['POST'])
def search_case():
    """Search within a case using Claude"""
    data = request.get_json()
    case_id = data.get('case_id')
    query = data.get('query')

    if not case_id or not query:
        return jsonify({'error': 'Case ID and query required'}), 400

    result = manager.search_case_with_claude(case_id, query)
    return jsonify(result)

@app.route('/api/create-case', methods=['POST'])
def create_case():
    """Create a new case folder structure"""
    data = request.get_json()
    case_id = data.get('case_id')

    if not case_id:
        return jsonify({'error': 'Case ID required'}), 400

    # Create folder structure
    categories = ['Documents', 'Phone-Extractions', 'Photos', 'Videos', 'Audio', 'Reports']

    for category in categories:
        # Create a placeholder file to establish the folder
        s3_key = f"{case_id}/{category}/.placeholder"
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=b'',
            Metadata={'created': datetime.now().isoformat()}
        )

    return jsonify({
        'success': True,
        'case_id': case_id,
        'structure': categories
    })

if __name__ == '__main__':
    print("🚀 Starting Simplified JIM AI - S3 Evidence Management")
    print(f"📦 S3 Bucket: {S3_BUCKET}")
    print(f"🌍 Region: {REGION}")
    print("💻 Open: http://localhost:8080")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=8080)