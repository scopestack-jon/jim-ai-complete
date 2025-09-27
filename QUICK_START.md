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

#### Option 1: Web Interface (≤100MB files)
- Open http://localhost:8080
- Click "📁 Upload Case Files"
- Drag & drop or select files
- Automatic processing and ingestion

#### Option 2: Large Cell Phone Data (150GB+)
```bash
# For large cell phone extractions
python3 large-data-processor.py /path/to/your/cell-phone-extraction

# Example:
python3 large-data-processor.py /Volumes/Evidence/iPhone_Case123
```

#### Option 3: Command Line (Legacy)
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

### Web Interface:
- **File size limit**: 100MB per file, 500MB total per upload
- **Supported formats**: PDF, DOCX, TXT, CSV, JSON, HTML, SQLite, ZIP
- **Automatic processing**: Files split to ≤50MB chunks for Knowledge Base

### Large Data Processor:
- **No size limits**: Handles 150GB+ cell phone extractions
- **SQLite conversion**: Automatically converts .db files to searchable CSV
- **Archive extraction**: Handles ZIP, TAR files automatically
- **Parallel processing**: 5 concurrent uploads for optimal speed

## ✅ What's Working

- ✅ AWS infrastructure fully configured
- ✅ Knowledge Base active and tested
- ✅ Web chat interface functional
- ✅ Document ingestion pipeline working
- ✅ Foundation model parser enabled

Ready for your real forensic data! 🔍