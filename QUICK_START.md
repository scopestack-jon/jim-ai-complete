# JIM AI - Quick Start Guide

## 🚀 Resume Your Work

### Start the Web App
```bash
cd /Users/jonscott/Downloads/jim-ai-complete
source jim-ai-env/bin/activate
python3 app.py
```
**Open**: http://localhost:8080

### Upload Your Forensic Data
```bash
# For cell phone/SQLite data
python3 preprocess-files.py /path/to/your/forensic-files

# Start ingestion after upload
aws bedrock-agent start-ingestion-job \
  --knowledge-base-id HFCMSKWHFU \
  --data-source-id CZJWLDWEFD \
  --region us-east-1
```

### Monitor Ingestion Status
```bash
# Check latest ingestion job
aws bedrock-agent list-ingestion-jobs \
  --knowledge-base-id HFCMSKWHFU \
  --data-source-id CZJWLDWEFD \
  --region us-east-1 \
  --max-results 1
```

## 📋 Key Information

**Knowledge Base ID**: `HFCMSKWHFU`
**Data Source ID**: `CZJWLDWEFD`
**S3 Bucket**: `jim-ai-forensic-data-1758988022`
**Upload Path**: `s3://jim-ai-forensic-data-1758988022/kb/`
**Web Interface**: http://localhost:8080

## 🔧 File Processing Tips

- **Keep files ≤50MB** each
- **Supported formats**: PDF, DOCX, TXT, CSV, JSON, HTML
- **SQLite exports**: Convert to CSV/JSON first
- **Large files**: Use the preprocessing script to split automatically

## ✅ What's Working

- ✅ AWS infrastructure fully configured
- ✅ Knowledge Base active and tested
- ✅ Web chat interface functional
- ✅ Document ingestion pipeline working
- ✅ Foundation model parser enabled

Ready for your real forensic data! 🔍