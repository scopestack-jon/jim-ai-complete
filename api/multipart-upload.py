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

@app.route('/api/multipart-upload/initiate', methods=['POST'])
def initiate_multipart_upload():
    """Initiate S3 multipart upload for large files"""
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
            
        if file_size > 100 * 1024 * 1024 * 1024:  # 100GB
            return jsonify({'error': 'File too large (max 100GB)'}), 400
        
        # Initialize S3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
            aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'],
            region_name=os.environ.get('AWS_REGION', 'us-east-1')
        )
        
        # Generate S3 key preserving original filename
        clean_filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        s3_key = f"jim-ai-uploads/{timestamp}_{clean_filename}"
        
        # Initiate multipart upload
        response = s3_client.create_multipart_upload(
            Bucket=os.environ['S3_BUCKET_NAME'],
            Key=s3_key,
            ContentType=file_type
        )
        
        upload_id = response['UploadId']
        file_id = str(uuid.uuid4())
        
        # Calculate chunk info
        chunk_size = 100 * 1024 * 1024  # 100MB chunks
        total_chunks = (file_size + chunk_size - 1) // chunk_size
        
        return jsonify({
            'upload_id': upload_id,
            'file_id': file_id,
            's3_key': s3_key,
            'chunk_size': chunk_size,
            'total_chunks': total_chunks
        })
        
    except ClientError as e:
        return jsonify({'error': f'AWS error: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/multipart-upload/chunk', methods=['POST'])
def get_chunk_upload_url():
    """Get pre-signed URL for uploading a specific chunk"""
    try:
        data = request.json
        upload_id = data.get('upload_id')
        s3_key = data.get('s3_key')
        part_number = data.get('part_number')  # 1-based
        
        if not all([upload_id, s3_key, part_number]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Initialize S3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
            aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'],
            region_name=os.environ.get('AWS_REGION', 'us-east-1')
        )
        
        # Generate pre-signed URL for this chunk
        presigned_url = s3_client.generate_presigned_url(
            'upload_part',
            Params={
                'Bucket': os.environ['S3_BUCKET_NAME'],
                'Key': s3_key,
                'UploadId': upload_id,
                'PartNumber': part_number
            },
            ExpiresIn=3600  # 1 hour
        )
        
        return jsonify({
            'upload_url': presigned_url,
            'part_number': part_number
        })
        
    except ClientError as e:
        return jsonify({'error': f'AWS error: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/multipart-upload/complete', methods=['POST'])
def complete_multipart_upload():
    """Complete multipart upload after all chunks are uploaded"""
    try:
        data = request.json
        upload_id = data.get('upload_id')
        s3_key = data.get('s3_key')
        parts = data.get('parts')  # List of {PartNumber, ETag}
        
        # File metadata
        file_id = data.get('file_id')
        filename = data.get('filename')
        file_size = data.get('file_size')
        file_type = data.get('file_type')
        case_id = data.get('case_id')
        description = data.get('description')
        
        if not all([upload_id, s3_key, parts, file_id]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Initialize S3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
            aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'],
            region_name=os.environ.get('AWS_REGION', 'us-east-1')
        )
        
        # Complete multipart upload
        response = s3_client.complete_multipart_upload(
            Bucket=os.environ['S3_BUCKET_NAME'],
            Key=s3_key,
            UploadId=upload_id,
            MultipartUpload={'Parts': parts}
        )
        
        # Save file metadata (reuse existing upload-complete logic)
        import json
        FILES_DB = 'files.json'
        
        def load_files():
            if os.path.exists(FILES_DB):
                with open(FILES_DB, 'r') as f:
                    return json.load(f)
            return []
        
        def save_files(files):
            with open(FILES_DB, 'w') as f:
                json.dump(files, f, indent=2)
        
        # Load existing files and add new record
        files = load_files()
        file_record = {
            'id': file_id,
            's3_key': s3_key,
            'filename': filename,
            'file_size': file_size,
            'file_type': file_type,
            'case_id': case_id,
            'description': description,
            'upload_date': datetime.now().isoformat(),
            'status': 'uploaded',
            'upload_type': 'multipart'
        }
        
        files.append(file_record)
        save_files(files)
        
        return jsonify({
            'success': True,
            'file_id': file_id,
            'status': 'uploaded',
            'etag': response.get('ETag')
        })
        
    except ClientError as e:
        return jsonify({'error': f'AWS error: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/multipart-upload/abort', methods=['POST'])
def abort_multipart_upload():
    """Abort multipart upload and clean up"""
    try:
        data = request.json
        upload_id = data.get('upload_id')
        s3_key = data.get('s3_key')
        
        if not all([upload_id, s3_key]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Initialize S3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
            aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'],
            region_name=os.environ.get('AWS_REGION', 'us-east-1')
        )
        
        # Abort multipart upload
        s3_client.abort_multipart_upload(
            Bucket=os.environ['S3_BUCKET_NAME'],
            Key=s3_key,
            UploadId=upload_id
        )
        
        return jsonify({'success': True, 'message': 'Upload aborted'})
        
    except ClientError as e:
        return jsonify({'error': f'AWS error: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# For Vercel
def handler(request):
    return app(request.environ, lambda status, headers: None)

if __name__ == '__main__':
    app.run(debug=True, port=5000)

