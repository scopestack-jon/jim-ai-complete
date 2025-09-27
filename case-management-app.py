#!/usr/bin/env python3
"""
JIM AI - Professional Case Management System
Each case gets its own S3 bucket with proper organization
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import boto3
import json
import os
from datetime import datetime, timezone
import pytz
from werkzeug.utils import secure_filename
import hashlib
import sqlite3
from pathlib import Path

app = Flask(__name__)
app.secret_key = 'jim-ai-case-management-2024'

# Configuration
REGION = "us-east-1"
ACCOUNT_ID = "447053376377"  # Your AWS account ID
DATABASE_PATH = "cases.db"

# AWS clients
s3_client = boto3.client('s3', region_name=REGION)
bedrock_client = boto3.client('bedrock-runtime', region_name=REGION)

class CaseManagementSystem:
    """Manage multiple cases with individual S3 buckets"""

    def __init__(self):
        self.init_database()

    def init_database(self):
        """Initialize SQLite database for case tracking"""
        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()

        # Create cases table
        c.execute('''CREATE TABLE IF NOT EXISTS cases
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     case_number TEXT UNIQUE NOT NULL,
                     client_name TEXT NOT NULL,
                     attorney_name TEXT,
                     timezone TEXT NOT NULL,
                     bucket_name TEXT UNIQUE NOT NULL,
                     created_date TEXT NOT NULL,
                     status TEXT DEFAULT 'active',
                     description TEXT,
                     metadata TEXT)''')

        # Create file tracking table
        c.execute('''CREATE TABLE IF NOT EXISTS case_files
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     case_number TEXT NOT NULL,
                     file_category TEXT NOT NULL,
                     file_name TEXT NOT NULL,
                     s3_key TEXT NOT NULL,
                     file_size INTEGER,
                     upload_date TEXT NOT NULL,
                     uploaded_by TEXT,
                     file_hash TEXT,
                     metadata TEXT,
                     FOREIGN KEY(case_number) REFERENCES cases(case_number))''')

        conn.commit()
        conn.close()

    def create_case(self, case_data):
        """Create a new case with its own S3 bucket"""
        try:
            # Generate unique bucket name (must be globally unique)
            case_number_clean = case_data['case_number'].lower().replace(' ', '-').replace('_', '-')
            client_name_clean = case_data['client_name'].lower().replace(' ', '-')[:10]
            timestamp = datetime.now().strftime('%Y%m%d')
            bucket_name = f"jim-ai-{client_name_clean}-{case_number_clean}-{timestamp}"

            # Ensure bucket name is valid (3-63 chars, lowercase, no underscores)
            bucket_name = ''.join(c for c in bucket_name if c.isalnum() or c == '-')[:63]

            # Create S3 bucket
            if REGION == 'us-east-1':
                s3_client.create_bucket(Bucket=bucket_name)
            else:
                s3_client.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': REGION}
                )

            # Enable versioning for evidence integrity
            s3_client.put_bucket_versioning(
                Bucket=bucket_name,
                VersioningConfiguration={'Status': 'Enabled'}
            )

            # Enable encryption
            s3_client.put_bucket_encryption(
                Bucket=bucket_name,
                ServerSideEncryptionConfiguration={
                    'Rules': [{
                        'ApplyServerSideEncryptionByDefault': {
                            'SSEAlgorithm': 'AES256'
                        }
                    }]
                }
            )

            # Block public access
            s3_client.put_public_access_block(
                Bucket=bucket_name,
                PublicAccessBlockConfiguration={
                    'BlockPublicAcls': True,
                    'IgnorePublicAcls': True,
                    'BlockPublicPolicy': True,
                    'RestrictPublicBuckets': True
                }
            )

            # Create folder structure
            folders = [
                'Documents/Legal/',
                'Documents/Reports/',
                'Documents/Correspondence/',
                'Phone-Extractions/iOS/',
                'Phone-Extractions/Android/',
                'Phone-Extractions/Processed/',
                'Digital-Evidence/Computers/',
                'Digital-Evidence/Cloud/',
                'Digital-Evidence/Social-Media/',
                'Multimedia/Photos/',
                'Multimedia/Videos/',
                'Multimedia/Audio/',
                'Analysis/Timeline/',
                'Analysis/Reports/',
                'Analysis/Expert-Opinions/'
            ]

            for folder in folders:
                s3_client.put_object(
                    Bucket=bucket_name,
                    Key=f"{folder}.placeholder",
                    Body=b'',
                    Metadata={
                        'case_number': case_data['case_number'],
                        'created': datetime.now(timezone.utc).isoformat()
                    }
                )

            # Save to database
            conn = sqlite3.connect(DATABASE_PATH)
            c = conn.cursor()

            c.execute('''INSERT INTO cases
                        (case_number, client_name, attorney_name, timezone, bucket_name,
                         created_date, description, metadata)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                     (case_data['case_number'],
                      case_data['client_name'],
                      case_data.get('attorney_name', session.get('username', 'Unknown')),
                      case_data['timezone'],
                      bucket_name,
                      datetime.now(timezone.utc).isoformat(),
                      case_data.get('description', ''),
                      json.dumps(case_data.get('metadata', {}))))

            conn.commit()
            conn.close()

            return {
                'success': True,
                'bucket_name': bucket_name,
                'case_number': case_data['case_number'],
                'message': f'Case {case_data["case_number"]} created successfully'
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def list_cases(self, attorney_name=None):
        """List all cases or cases for specific attorney"""
        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()

        if attorney_name:
            c.execute('''SELECT * FROM cases WHERE attorney_name = ? AND status = 'active'
                        ORDER BY created_date DESC''', (attorney_name,))
        else:
            c.execute('''SELECT * FROM cases WHERE status = 'active'
                        ORDER BY created_date DESC''')

        cases = []
        for row in c.fetchall():
            cases.append({
                'id': row[0],
                'case_number': row[1],
                'client_name': row[2],
                'attorney_name': row[3],
                'timezone': row[4],
                'bucket_name': row[5],
                'created_date': row[6],
                'status': row[7],
                'description': row[8]
            })

        conn.close()
        return cases

    def get_case_details(self, case_number):
        """Get detailed information about a case"""
        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()

        # Get case info
        c.execute('SELECT * FROM cases WHERE case_number = ?', (case_number,))
        case_row = c.fetchone()

        if not case_row:
            conn.close()
            return None

        case_info = {
            'case_number': case_row[1],
            'client_name': case_row[2],
            'attorney_name': case_row[3],
            'timezone': case_row[4],
            'bucket_name': case_row[5],
            'created_date': case_row[6],
            'status': case_row[7],
            'description': case_row[8]
        }

        # Get file statistics
        c.execute('''SELECT file_category, COUNT(*), SUM(file_size)
                    FROM case_files
                    WHERE case_number = ?
                    GROUP BY file_category''', (case_number,))

        file_stats = {}
        total_files = 0
        total_size = 0

        for row in c.fetchall():
            file_stats[row[0]] = {
                'count': row[1],
                'size': row[2] or 0
            }
            total_files += row[1]
            total_size += row[2] or 0

        case_info['file_statistics'] = file_stats
        case_info['total_files'] = total_files
        case_info['total_size'] = total_size

        # Get recent uploads
        c.execute('''SELECT file_name, file_category, upload_date, file_size
                    FROM case_files
                    WHERE case_number = ?
                    ORDER BY upload_date DESC
                    LIMIT 10''', (case_number,))

        recent_files = []
        for row in c.fetchall():
            recent_files.append({
                'name': row[0],
                'category': row[1],
                'upload_date': row[2],
                'size': row[3]
            })

        case_info['recent_files'] = recent_files

        conn.close()
        return case_info

    def upload_file(self, case_number, category, file_obj, filename, uploaded_by=None):
        """Upload a file to the appropriate case bucket and category"""
        try:
            # Get case info
            conn = sqlite3.connect(DATABASE_PATH)
            c = conn.cursor()
            c.execute('SELECT bucket_name, timezone FROM cases WHERE case_number = ?', (case_number,))
            case_row = c.fetchone()

            if not case_row:
                conn.close()
                return {'success': False, 'error': 'Case not found'}

            bucket_name = case_row[0]
            case_timezone = case_row[1]

            # Create S3 key
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_filename = secure_filename(filename)
            s3_key = f"{category}/{timestamp}_{safe_filename}"

            # Calculate file hash
            file_content = file_obj.read()
            file_hash = hashlib.sha256(file_content).hexdigest()
            file_size = len(file_content)
            file_obj.seek(0)  # Reset file pointer

            # Upload to S3
            s3_client.upload_fileobj(
                file_obj,
                bucket_name,
                s3_key,
                ExtraArgs={
                    'Metadata': {
                        'case_number': case_number,
                        'category': category,
                        'original_name': filename,
                        'uploaded_by': uploaded_by or 'Unknown',
                        'upload_time': datetime.now(timezone.utc).isoformat(),
                        'file_hash': file_hash,
                        'timezone': case_timezone
                    }
                }
            )

            # Record in database
            c.execute('''INSERT INTO case_files
                        (case_number, file_category, file_name, s3_key, file_size,
                         upload_date, uploaded_by, file_hash)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                     (case_number, category, filename, s3_key, file_size,
                      datetime.now(timezone.utc).isoformat(),
                      uploaded_by or 'Unknown', file_hash))

            conn.commit()
            conn.close()

            return {
                'success': True,
                'file_name': filename,
                's3_key': s3_key,
                'file_size': file_size,
                'file_hash': file_hash
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def convert_timezone(self, utc_time, target_timezone):
        """Convert UTC timestamp to case timezone"""
        utc_dt = datetime.fromisoformat(utc_time.replace('Z', '+00:00'))
        target_tz = pytz.timezone(target_timezone)
        return utc_dt.astimezone(target_tz)

    def search_case_with_ai(self, case_number, query, include_timezone_conversion=True):
        """Search case files using AI with timezone awareness"""
        try:
            case_info = self.get_case_details(case_number)
            if not case_info:
                return {'error': 'Case not found'}

            # Get file list from database
            conn = sqlite3.connect(DATABASE_PATH)
            c = conn.cursor()
            c.execute('''SELECT file_name, file_category, s3_key, upload_date
                        FROM case_files
                        WHERE case_number = ?
                        ORDER BY upload_date DESC
                        LIMIT 20''', (case_number,))

            files = c.fetchall()
            conn.close()

            # Build context
            timezone_info = f"Case timezone: {case_info['timezone']}" if include_timezone_conversion else ""

            context = f"""
            Case Information:
            - Case Number: {case_info['case_number']}
            - Client: {case_info['client_name']}
            - Attorney: {case_info['attorney_name']}
            - {timezone_info}
            - Total Files: {case_info['total_files']}
            - Categories: {', '.join(case_info['file_statistics'].keys())}

            File Overview:
            """

            for file in files:
                context += f"\n- {file[0]} (Category: {file[1]}, Uploaded: {file[3]})"

            # Query Claude
            prompt = f"""You are a legal forensic assistant. Based on the case information provided,
            answer the following query: {query}

            {context}

            Important: All phone data timestamps are originally in UTC. The case timezone is {case_info['timezone']}.
            Convert any timestamps to the case timezone when discussing times.

            Provide a clear, legally-focused answer."""

            response = bedrock_client.invoke_model(
                modelId='anthropic.claude-3-5-sonnet-20240620-v1:0',
                contentType='application/json',
                accept='application/json',
                body=json.dumps({
                    'anthropic_version': 'bedrock-2023-05-31',
                    'max_tokens': 2000,
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
                'case_number': case_number,
                'files_available': len(files),
                'timezone': case_info['timezone']
            }

        except Exception as e:
            return {'error': str(e)}

# Initialize system
case_system = CaseManagementSystem()

# Flask routes
@app.route('/')
def index():
    """Main dashboard"""
    return render_template('case_dashboard.html')

@app.route('/api/cases', methods=['GET'])
def list_cases():
    """Get all cases for current attorney"""
    attorney = session.get('username', None)
    cases = case_system.list_cases(attorney)
    return jsonify(cases)

@app.route('/api/case/<case_number>', methods=['GET'])
def get_case(case_number):
    """Get detailed case information"""
    case_info = case_system.get_case_details(case_number)
    if case_info:
        return jsonify(case_info)
    return jsonify({'error': 'Case not found'}), 404

@app.route('/api/case', methods=['POST'])
def create_case():
    """Create a new case"""
    data = request.get_json()

    required_fields = ['case_number', 'client_name', 'timezone']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400

    result = case_system.create_case(data)
    if result['success']:
        return jsonify(result)
    return jsonify(result), 500

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Upload file to a case"""
    case_number = request.form.get('case_number')
    category = request.form.get('category', 'Documents/General')

    if not case_number:
        return jsonify({'error': 'Case number required'}), 400

    uploaded_files = []
    for file in request.files.getlist('files'):
        if file:
            result = case_system.upload_file(
                case_number,
                category,
                file,
                file.filename,
                session.get('username', 'Unknown')
            )
            uploaded_files.append(result)

    return jsonify({
        'uploaded': uploaded_files,
        'case_number': case_number,
        'category': category
    })

@app.route('/api/search', methods=['POST'])
def search_case():
    """AI-powered case search"""
    data = request.get_json()
    case_number = data.get('case_number')
    query = data.get('query')

    if not case_number or not query:
        return jsonify({'error': 'Case number and query required'}), 400

    result = case_system.search_case_with_ai(case_number, query)
    return jsonify(result)

@app.route('/api/timezones', methods=['GET'])
def get_timezones():
    """Get list of common timezones"""
    common_timezones = [
        'US/Eastern',
        'US/Central',
        'US/Mountain',
        'US/Pacific',
        'US/Alaska',
        'US/Hawaii',
        'Europe/London',
        'Europe/Paris',
        'Asia/Tokyo',
        'Australia/Sydney'
    ]
    return jsonify(common_timezones)

if __name__ == '__main__':
    print("🚀 Starting JIM AI Case Management System")
    print("📊 Database: cases.db")
    print("🌍 Region: " + REGION)
    print("💼 Professional legal case management")
    print("💻 Open: http://localhost:8080")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=8080)