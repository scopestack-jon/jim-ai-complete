import boto3
import uuid
import os
import re
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from botocore.exceptions import ClientError

app = Flask(__name__)
CORS(app)

@app.route('/api/upload-url', methods=['POST'])
def generate_upload_url():
    """Generate pre-signed URL for S3 upload"""
    try:
        data = request.json
        filename = data.get('filename')
        file_size = data.get('file_size', 0)
        file_type = data.get('file_type', '')
        case_id = data.get('case_id')
        description = data.get('description')
        
        # Validate file
        if not filename:
            return jsonify({'error': 'Filename is required'}), 400
            
        if file_size > 500 * 1024 * 1024:  # 500MB
            return jsonify({'error': 'File too large'}), 400
        
        # Initialize S3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
            aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'],
            region_name=os.environ.get('AWS_REGION', 'us-east-1')
        )
        
        # Generate S3 key preserving original filename
        # Clean filename to be S3-safe (remove special characters, spaces)
        clean_filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
        
        # Add timestamp prefix to avoid conflicts while keeping readable name
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        s3_key = f"jim-ai-uploads/{timestamp}_{clean_filename}"
        
        # Generate pre-signed URL
        presigned_url = s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': os.environ['S3_BUCKET_NAME'],
                'Key': s3_key,
                'ContentType': file_type
            },
            ExpiresIn=3600  # 1 hour
        )
        
        file_id = str(uuid.uuid4())
        
        return jsonify({
            'upload_url': presigned_url,
            'file_id': file_id,
            's3_key': s3_key,
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

