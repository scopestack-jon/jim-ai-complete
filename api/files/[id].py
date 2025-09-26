import os
import json
import boto3
from flask import Flask, jsonify, request
from flask_cors import CORS
from botocore.exceptions import ClientError

app = Flask(__name__)
CORS(app)

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

def find_file_by_id(file_id):
    """Find file by ID"""
    files = load_files()
    return next((f for f in files if f['id'] == file_id), None)

@app.route('/api/files/<file_id>', methods=['GET'])
def get_file(file_id):
    """Get file metadata"""
    try:
        file_record = find_file_by_id(file_id)
        if not file_record:
            return jsonify({'error': 'File not found'}), 404
            
        return jsonify(file_record)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/files/<file_id>', methods=['DELETE'])
def delete_file(file_id):
    """Delete file from S3 and database"""
    try:
        files = load_files()
        file_record = find_file_by_id(file_id)
        
        if not file_record:
            return jsonify({'error': 'File not found'}), 404
        
        # Delete from S3
        try:
            s3_client = boto3.client(
                's3',
                aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
                aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'],
                region_name=os.environ.get('AWS_REGION', 'us-east-1')
            )
            
            s3_client.delete_object(
                Bucket=os.environ['S3_BUCKET_NAME'],
                Key=file_record['s3_key']
            )
        except ClientError as e:
            print(f"S3 delete error: {e}")
            # Continue with database deletion even if S3 fails
        
        # Remove from database
        files = [f for f in files if f['id'] != file_id]
        save_files(files)
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# For Vercel
def handler(request):
    return app(request.environ, lambda status, headers: None)

if __name__ == '__main__':
    app.run(debug=True, port=5000)

