import os
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/api/config', methods=['GET'])
def get_config():
    """Get upload configuration"""
    return jsonify({
        'max_file_size': 100 * 1024 * 1024 * 1024,  # 100GB
        'chunk_size': 100 * 1024 * 1024,  # 100MB chunks for multipart upload
        'multipart_threshold': 1024 * 1024 * 1024,  # Use multipart for files > 1GB
        'allowed_extensions': [
            # Documents
            'pdf', 'doc', 'docx', 'txt', 'rtf',
            # Images  
            'jpg', 'jpeg', 'png', 'tiff', 'bmp', 'gif', 'pst',
            # Audio
            'mp3', 'wav', 'm4a', 'aac', 'flac',
            # Video
            'mp4', 'avi', 'mov', 'wmv', 'mkv', 'mp4', 'rar', 'mdb',
            # Archives
            'zip', '7z', 'tar', 'gz', 'sqlite',
            # Email
            'eml', 'msg',
            # Database
            'db', 'sql', 'docx', 'gif', 'jpeg', 'wmv'
        ],
        's3_configured': bool(os.environ.get('AWS_ACCESS_KEY_ID'))
    })

# For Vercel
def handler(request):
    return app(request.environ, lambda status, headers: None)

if __name__ == '__main__':
    app.run(debug=True, port=5000)

