# JIM AI - Troubleshooting Guide

## 🚨 Common Issues and Solutions

### 1. Upload/Processing Failures

#### **Problem**: "AccessDenied" when uploading files
**Symptoms**:
- Files fail to upload through web interface
- Error: `User is not authorized to perform: s3:ListBucket`

**Solution**: Fix IAM permissions
1. Go to [IAM Users Console](https://console.aws.amazon.com/iam/home#/users/jim-ai-s3-user)
2. Click "Permissions" tab → "Add permissions" → "Attach policies directly"
3. Add this policy:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:ListBucket",
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject"
            ],
            "Resource": [
                "arn:aws:s3:::jim-ai-forensic-data-1758988022",
                "arn:aws:s3:::jim-ai-forensic-data-1758988022/*"
            ]
        }
    ]
}
```

#### **Problem**: Ingestion jobs fail with "object mapping" error
**Symptoms**:
- Files upload successfully but processing fails
- Error: `object mapping for [AMAZON_BEDROCK_METADATA] tried to parse field as object`

**Solution**: Fix OpenSearch index mapping
1. Go to [OpenSearch Serverless Console](https://us-east-1.console.aws.amazon.com/aos/home?region=us-east-1#opensearch/collections)
2. Click collection `bedrock-knowledge-base-j2lnf2`
3. Click "Query workbench" tab
4. Run these commands:

```sql
DELETE /bedrock-kb-index

PUT /bedrock-kb-index
{
  "mappings": {
    "properties": {
      "bedrock-knowledge-base-default-vector": {
        "type": "knn_vector",
        "dimension": 1024
      },
      "AMAZON_BEDROCK_TEXT_CHUNK": {
        "type": "text"
      }
    }
  }
}
```

### 2. Configuration Issues

#### **Problem**: Wrong S3 bucket configured
**Symptoms**:
- Upload works but files don't appear in Knowledge Base
- Mixed bucket names in configuration

**Solution**: Ensure consistent bucket configuration
- **Correct bucket**: `jim-ai-forensic-data-1758988022`
- **Check**: `app.py` line 24: `S3_BUCKET = "jim-ai-forensic-data-1758988022"`
- **Check**: `.env` file: `S3_BUCKET_NAME=jim-ai-forensic-data-1758988022`

#### **Problem**: AWS credentials not working
**Symptoms**:
- "Access denied" errors
- "Invalid credentials" messages

**Solution**: Verify AWS configuration
1. Check `.env` file has correct credentials
2. Test with: `aws s3 ls s3://jim-ai-forensic-data-1758988022/`
3. If needed, run: `aws configure` to reset credentials

### 3. Web Interface Issues

#### **Problem**: Web interface won't load
**Symptoms**:
- Browser shows "This site can't be reached"
- Connection refused errors

**Solutions**:
1. **Wait 30 seconds** after starting the application
2. Try `http://127.0.0.1:8080` instead of `localhost:8080`
3. Check if port 8080 is in use: `lsof -i :8080`
4. Restart the application: Double-click `Start_JIM_AI.command`

#### **Problem**: Files won't upload through web interface
**Symptoms**:
- Drag & drop doesn't work
- "File too large" errors for small files

**Solutions**:
1. **File size**: Max 100MB per file for web interface
2. **File types**: Must be PDF, DOCX, TXT, CSV, JSON, SQLite, ZIP, etc.
3. **Large data**: Use `large-data-processor.py` for files >100MB
4. **Browser**: Try different browser (Chrome, Safari, Firefox)

### 4. Large Data Processing Issues

#### **Problem**: Large data processor fails
**Symptoms**:
- Script exits with errors
- "Out of memory" or "No space left" errors

**Solutions**:
1. **Disk space**: Ensure 3x your data size available
2. **Memory**: 8GB+ RAM recommended for 150GB datasets
3. **Permissions**: Run `chmod +x large-data-processor.py`
4. **Path**: Use absolute paths: `/full/path/to/data`

#### **Problem**: SQLite conversion fails
**Symptoms**:
- "Database is locked" errors
- "Corruption" messages

**Solutions**:
1. **Copy files first**: `cp locked.db unlocked.db`
2. **Close applications** that might be using the database
3. **Check file permissions**: `ls -la *.db`

### 5. Processing Time Expectations

| Data Size | Upload Time | Processing Time | Total Time |
|-----------|-------------|-----------------|------------|
| 100MB | 2-5 minutes | 5-10 minutes | 7-15 minutes |
| 1GB | 5-15 minutes | 10-20 minutes | 15-35 minutes |
| 10GB | 30-60 minutes | 20-40 minutes | 50-100 minutes |
| 100GB | 3-6 hours | 1-2 hours | 4-8 hours |

### 6. Status Checking Commands

```bash
# Check ingestion status
aws bedrock-agent list-ingestion-jobs \
  --knowledge-base-id HFCMSKWHFU \
  --data-source-id CZJWLDWEFD \
  --region us-east-1 \
  --max-results 1

# Check web service status
curl http://localhost:8080/api/status

# Check S3 bucket access
aws s3 ls s3://jim-ai-forensic-data-1758988022/kb/

# Check Knowledge Base details
aws bedrock-agent get-knowledge-base \
  --knowledge-base-id HFCMSKWHFU \
  --region us-east-1
```

### 7. Emergency Recovery

#### **Start Fresh**:
1. Stop all running processes: `pkill -f "python3 app.py"`
2. Clear temporary files: `rm -rf /tmp/claude/*`
3. Restart: Double-click `Start_JIM_AI.command`

#### **Reset Knowledge Base**:
1. Delete and recreate OpenSearch index (see above)
2. Re-upload files through web interface
3. Wait for processing to complete

### 8. Getting Help

#### **Check Logs**:
- Web interface: Browser developer console (F12)
- Command line: Terminal output from running scripts
- AWS: CloudWatch logs for Bedrock and OpenSearch

#### **Support Resources**:
- `USER_GUIDE.md` - Step-by-step instructions
- `LARGE_DATA_GUIDE.md` - Comprehensive processing guide
- `QUICK_START.md` - Command reference

#### **Common Error Patterns**:
- **403 Forbidden** → IAM permissions issue
- **404 Not Found** → Index or bucket doesn't exist
- **400 Bad Request** → Invalid file format or size
- **500 Internal Error** → AWS service or configuration issue

---

**Remember**: Most issues are either **permissions** (IAM/S3) or **configuration** (bucket names, index mapping). Follow the solutions above systematically! 🛠️