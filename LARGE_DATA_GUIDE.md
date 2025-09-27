# Large Cell Phone Data Processing Guide

## 📱 For 150GB+ Cell Phone Extractions

### Quick Start for Large Data

```bash
# Navigate to project directory
cd /Users/jonscott/Downloads/jim-ai-complete

# Activate Python environment
source jim-ai-env/bin/activate

# Process large cell phone extraction
python3 large-data-processor.py /path/to/your/cell-phone-extraction
```

## 🎯 Two Upload Methods

### Method 1: Web Interface (≤100MB files)
- **Best for**: Documents, small databases, individual files
- **Access**: http://localhost:8080 → "📁 Upload Case Files"
- **Limits**: 100MB per file, 500MB total per upload
- **Features**: Drag & drop, progress tracking, real-time status

### Method 2: Large Data Processor (150GB+)
- **Best for**: Complete cell phone extractions, large SQLite databases
- **Command**: `python3 large-data-processor.py /path/to/data`
- **Features**: Parallel processing, SQLite conversion, automatic chunking

## 📂 Supported Cell Phone Data Types

### Automatically Processed:
- **SQLite Databases** → Converted to CSV files
  - `messages.db` → `messages.csv`
  - `contacts.sqlite` → `contacts.csv`
  - `call_history.db` → Multiple table CSVs

- **Archive Files** → Extracted and processed
  - `.zip`, `.tar`, `.tar.gz` files
  - Nested archives supported

- **Large Files** → Split into 50MB chunks
  - Maintains file integrity
  - Optimized for Knowledge Base ingestion

### File Types Supported:
```
Documents: PDF, DOCX, TXT, HTML, XML
Data: CSV, JSON, SQLite (.db, .sqlite, .sqlite3)
Archives: ZIP, TAR, TAR.GZ
```

## 🚀 Large Data Processing Workflow

### 1. Prepare Your Data
```bash
# Example cell phone extraction structure:
/Volumes/Evidence/iPhone_Case123/
├── Databases/
│   ├── SMS.db           # 2.5GB
│   ├── Contacts.db      # 500MB
│   └── CallHistory.db   # 1.2GB
├── Media/
│   ├── Photos.zip       # 45GB
│   └── Videos.tar.gz    # 78GB
└── Applications/
    ├── WhatsApp.db      # 8.2GB
    └── Signal.db        # 3.1GB
```

### 2. Run Large Data Processor
```bash
python3 large-data-processor.py /Volumes/Evidence/iPhone_Case123/
```

**What it does:**
- Scans entire directory structure
- Converts SQLite databases to searchable CSV format
- Extracts and processes archives
- Splits large files into Knowledge Base compatible chunks
- Uploads files in parallel (5 concurrent threads)
- Starts Knowledge Base ingestion automatically

### 3. Monitor Progress
```
🔍 Processing large cell phone extraction: /Volumes/Evidence/iPhone_Case123/
📊 Scanning directory structure...
Processing: SMS.db (2456.8MB)
Processing: Contacts.db (487.3MB)
Processing: CallHistory.db (1158.2MB)
...
📦 Total files to upload: 1,847
✅ Uploaded 1,245/1,847: SMS_messages.csv
✅ Uploaded 1,246/1,847: SMS_attachments.csv
...
📊 Upload Summary:
   ✅ Successful: 1,834
   ❌ Failed: 13
   📈 Success rate: 99.3%
🚀 Starting Knowledge Base ingestion...
✅ Ingestion job started: a1b2c3d4-e5f6-7890-abcd-1234567890ef
⏳ Processing will take 15-45 minutes for large datasets
```

### 4. Query Your Data
- **Web Interface**: http://localhost:8080
- **Wait Time**: 15-45 minutes for 150GB datasets
- **Status Check**: Monitor ingestion in web interface

## 📊 Performance Expectations

| Data Size | Processing Time | Upload Time | Ingestion Time | Total Time |
|-----------|----------------|-------------|----------------|------------|
| 1GB       | 2-5 minutes    | 3-8 minutes | 5-10 minutes   | 10-23 min  |
| 10GB      | 8-15 minutes   | 15-30 min   | 10-20 minutes  | 33-65 min  |
| 50GB      | 25-45 minutes  | 45-90 min   | 20-35 minutes  | 90-170 min |
| 150GB     | 60-120 minutes | 2-4 hours   | 30-60 minutes  | 3.5-6 hours|

## 🔍 Example Queries After Processing

Once your cell phone data is processed, you can ask questions like:

- **"What text messages were sent on March 15th?"**
- **"Show me all contacts with phone numbers containing 555"**
- **"What calls were made between 10 PM and 6 AM?"**
- **"Find WhatsApp conversations mentioning 'meeting'"**
- **"List all deleted messages that were recovered"**
- **"What photos were taken at GPS coordinates near downtown?"**

## ⚠️ Important Notes

### Storage Requirements:
- **Local**: ~2x source data size during processing
- **S3**: ~1.5x source data size (after compression/chunking)
- **Temporary**: Uses `/tmp/claude/` for processing

### Memory Usage:
- **Recommended**: 8GB+ RAM for 150GB datasets
- **Minimum**: 4GB RAM for smaller datasets
- **Processing**: Handles files in chunks to minimize memory usage

### Network:
- **Upload Speed**: Dependent on internet connection
- **Parallel Transfers**: 5 concurrent uploads for optimal speed
- **Retry Logic**: Automatic retry with exponential backoff

## 🛠️ Troubleshooting

### Common Issues:

**"Error: Directory not found"**
```bash
# Ensure path is correct and accessible
ls -la /path/to/your/data
```

**"Upload failed: Access Denied"**
```bash
# Check AWS credentials
aws s3 ls s3://jim-ai-forensic-data-1758988022/
```

**"SQLite database is locked"**
```bash
# Copy database first, then process
cp locked.db unlocked.db
python3 large-data-processor.py /path/to/directory/
```

**"Out of disk space"**
```bash
# Clean up /tmp/claude/ directory
rm -rf /tmp/claude/large_processing/
```

### Performance Optimization:

**For faster processing:**
- Use SSD storage for source data
- Close other applications during processing
- Use wired internet connection for uploads
- Process during off-peak hours for better upload speeds

**For very large datasets (>500GB):**
- Consider processing in batches by subdirectory
- Monitor system resources during processing
- Ensure adequate disk space (3x source data size)

## 📞 Support

If you encounter issues with large data processing:

1. **Check Logs**: Look for error messages in console output
2. **Verify Connectivity**: Test AWS S3 access
3. **Monitor Resources**: Check disk space and memory usage
4. **Restart if Needed**: The processor can resume from where it left off

Your forensic analysis capabilities are now ready for the largest cell phone extractions! 🚀