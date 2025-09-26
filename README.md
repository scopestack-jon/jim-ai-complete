# JIM AI - Forensic Analyst Agent for Legal Teams

A complete web application for secure forensic file upload and management, designed specifically for legal teams.

## Features

- 🔒 **Secure File Upload** - Direct-to-S3 uploads with pre-signed URLs
- 📁 **Comprehensive File Support** - Documents, images, audio, video, archives, email, databases
- 🏢 **Case Management** - Organize files by case ID with descriptions
- 📱 **Responsive Design** - Works on desktop, tablet, and mobile
- ⚡ **Real-time Progress** - Upload progress tracking and status updates
- 🛡️ **Enterprise Security** - AWS S3 encryption, private buckets, minimal permissions

## Quick Start

### 1. Prerequisites
- Node.js 18+ and npm/pnpm
- Python 3.9+ and pip
- AWS account with S3 access

### 2. Environment Setup
```bash
# Clone or extract the project
cd jim-ai-complete

# Copy environment template
cp .env.example .env

# Edit .env with your AWS credentials
# AWS_ACCESS_KEY_ID=your_access_key
# AWS_SECRET_ACCESS_KEY=your_secret_key
# AWS_REGION=us-east-1
# S3_BUCKET_NAME=your-bucket-name
```

### 3. Install Dependencies
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies
npm install
# or
pnpm install
```

### 4. Run Locally
```bash
# Terminal 1: Start the API server
python local-server.py

# Terminal 2: Start the frontend
npm run dev
# or
pnpm dev
```

Visit http://localhost:5173 to use the application.

## Project Structure

```
jim-ai-complete/
├── api/                    # Backend API endpoints (Vercel Functions)
│   ├── config.py          # Upload configuration
│   ├── upload-url.py      # Generate pre-signed upload URLs
│   ├── upload-complete.py # Mark uploads complete
│   ├── files.py           # List files
│   ├── files/[id].py      # Individual file operations
│   └── download-url/[id].py # Generate download URLs
├── src/                   # Frontend React application
│   ├── components/ui/     # UI components (shadcn/ui)
│   ├── lib/              # Utility functions
│   ├── App.jsx           # Main application component
│   └── main.jsx          # Entry point
├── public/               # Static assets
├── local-server.py       # Local development server
├── vercel.json          # Vercel deployment configuration
├── package.json         # Node.js dependencies
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## AWS Setup

### 1. Create S3 Bucket
1. Go to AWS S3 Console
2. Create bucket with a unique name
3. Keep "Block Public Access" enabled
4. Enable default encryption

### 2. Configure CORS
Add this CORS configuration to your S3 bucket:
```json
[
    {
        "AllowedHeaders": ["*"],
        "AllowedMethods": ["GET", "PUT", "POST", "DELETE"],
        "AllowedOrigins": ["*"],
        "ExposeHeaders": ["ETag"]
    }
]
```

### 3. Create IAM User
1. Create IAM user with programmatic access
2. Attach this policy (replace bucket name):
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject"
            ],
            "Resource": "arn:aws:s3:::your-bucket-name/jim-ai-uploads/*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:ListBucket"
            ],
            "Resource": "arn:aws:s3:::your-bucket-name",
            "Condition": {
                "StringLike": {
                    "s3:prefix": "jim-ai-uploads/*"
                }
            }
        }
    ]
}
```

## Deployment

### Vercel (Recommended)
1. Install Vercel CLI: `npm i -g vercel`
2. Run: `vercel`
3. Set environment variables in Vercel dashboard
4. Deploy: `vercel --prod`

### Other Platforms
- **Frontend**: Can be deployed to Netlify, Vercel, or any static hosting
- **Backend**: Can be deployed to Heroku, Railway, or any Python hosting platform

## Environment Variables

Required environment variables:
```env
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-bucket-name
SECRET_KEY=your_flask_secret_key
```

## File Storage

Files are stored in S3 with this structure:
```
your-bucket/
└── jim-ai-uploads/
    └── 2024/
        └── 08/
            └── 19/
                ├── uuid1.pdf
                ├── uuid2.jpg
                └── uuid3.docx
```

## Supported File Types

- **Documents**: PDF, DOC, DOCX, TXT, RTF
- **Images**: JPG, JPEG, PNG, TIFF, BMP, GIF
- **Audio**: MP3, WAV, M4A, AAC, FLAC
- **Video**: MP4, AVI, MOV, WMV, MKV
- **Archives**: ZIP, RAR, 7Z, TAR, GZ
- **Email**: PST, EML, MSG
- **Database**: DB, SQL, MDB, SQLITE

## Security Features

- Private S3 bucket with no public access
- Pre-signed URLs with 1-hour expiration
- File type and size validation
- Minimal IAM permissions
- CORS protection
- Environment-based configuration

## Development

### Adding New File Types
Edit `api/config.py` and add extensions to `allowed_extensions` array.

### Modifying Upload Limits
Change `max_file_size` in `api/config.py` (default: 500MB).

### Database Integration
Replace the JSON file storage in the API endpoints with your preferred database (PostgreSQL, MySQL, etc.).

## Troubleshooting

### Common Issues

**"AWS credentials not found"**
- Check your .env file has the correct AWS credentials
- Ensure environment variables are set in deployment platform

**"Bucket not found"**
- Verify bucket name in environment variables
- Check bucket exists and you have access

**"CORS errors"**
- Ensure CORS is configured correctly on your S3 bucket
- Check allowed origins match your domain

**"File upload fails"**
- Check file size is under limit (500MB default)
- Verify file type is in allowed extensions
- Check AWS credentials have S3 permissions

### Getting Help
- Check browser console for frontend errors
- Check server logs for backend errors
- Verify AWS credentials with AWS CLI: `aws s3 ls s3://your-bucket`

## License

This project is provided as-is for educational and commercial use.

## Support

For issues or questions, check the troubleshooting section above or review the AWS and Vercel documentation for deployment-specific issues.

