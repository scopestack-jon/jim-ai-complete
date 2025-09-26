import os
import json
import boto3
from flask import Flask, jsonify
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

def find_file_by_id(file_id):
    """Find file by ID"""
    files = load_files()
    return next((f for f in files if f['id'] == file_id), None)

@app.route('/api/files/<file_id>/download-url', methods=['GET'])
def generate_download_url(file_id):
    """Generate pre-signed URL for file download"""
    try:
        file_record = find_file_by_id(file_id)
        if not file_record:
            return jsonify({'error': 'File not found'}), 404
        
        # Initialize S3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
            aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'],
            region_name=os.environ.get('AWS_REGION', 'us-east-1')
        )
        
        # Generate pre-signed URL for download
        download_url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': os.environ['S3_BUCKET_NAME'],
                'Key': file_record['s3_key'],
                'ResponseContentDisposition': f'attachment; filename="{file_record["filename"]}"'
            },
            ExpiresIn=3600  # 1 hour
        )
        
        return jsonify({
            'download_url': download_url,
            'filename': file_record['filename'],
            'expires_in': 3600
        })
        
    except ClientError as e:
        return jsonify({'error': f'AWS error: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# For Vercel
def handler(request):
    return app(request.environ, lambda status, headers: None)

if __name__ == '__main__':
    app.run(debug=True, port=5000)

