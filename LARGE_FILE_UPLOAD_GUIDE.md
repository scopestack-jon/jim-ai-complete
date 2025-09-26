# Large File Upload Guide (50-100GB Support)

## 🎯 **Overview**
This system now supports uploading files up to **100GB** using AWS S3 multipart uploads with chunking, progress tracking, and automatic retry logic.

## 📊 **Configuration Changes**

### Updated Limits:
- **Max file size**: 100GB (was 500MB)
- **Chunk size**: 100MB per chunk
- **Multipart threshold**: Files > 1GB use multipart upload
- **Concurrent uploads**: 3 chunks simultaneously
- **Retry attempts**: 3 attempts per chunk

## 🔧 **How It Works**

### 1. **Automatic Upload Strategy**
```javascript
if (file.size > 1GB) {
    // Use multipart upload (chunked)
    uploadLargeFile(file);
} else {
    // Use single-part upload (existing system)
    uploadSmallFile(file);
}
```

### 2. **Multipart Upload Process**
1. **Initiate**: Create multipart upload session
2. **Chunk**: Split file into 100MB pieces
3. **Upload**: Upload chunks in parallel (3 at a time)
4. **Complete**: Combine chunks into final file
5. **Cleanup**: Abort on failure to prevent orphaned chunks

### 3. **Progress Tracking**
- Real-time progress updates per chunk
- Concurrent upload monitoring
- Retry logic with exponential backoff
- Automatic cleanup on failure

## 🚀 **API Endpoints**

### New Multipart Endpoints:
- `POST /api/multipart-upload/initiate` - Start multipart upload
- `POST /api/multipart-upload/chunk` - Get chunk upload URL
- `POST /api/multipart-upload/complete` - Finalize upload
- `POST /api/multipart-upload/abort` - Cancel and cleanup

### Example API Usage:

#### 1. Initiate Upload
```bash
curl -X POST http://localhost:5001/api/multipart-upload/initiate \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "large-evidence.zip",
    "file_size": 53687091200,
    "file_type": "application/zip",
    "case_id": "CASE-001"
  }'
```

Response:
```json
{
  "upload_id": "abc123...",
  "file_id": "uuid...",
  "s3_key": "jim-ai-uploads/20250819_151933_large-evidence.zip",
  "chunk_size": 104857600,
  "total_chunks": 512
}
```

#### 2. Get Chunk Upload URL
```bash
curl -X POST http://localhost:5001/api/multipart-upload/chunk \
  -H "Content-Type: application/json" \
  -d '{
    "upload_id": "abc123...",
    "s3_key": "jim-ai-uploads/20250819_151933_large-evidence.zip",
    "part_number": 1
  }'
```

#### 3. Upload Chunk
```bash
curl -X PUT "https://s3-presigned-url..." \
  --data-binary @chunk-001.bin \
  -H "Content-Type: application/octet-stream"
```

#### 4. Complete Upload
```bash
curl -X POST http://localhost:5001/api/multipart-upload/complete \
  -H "Content-Type: application/json" \
  -d '{
    "upload_id": "abc123...",
    "s3_key": "jim-ai-uploads/20250819_151933_large-evidence.zip",
    "parts": [
      {"PartNumber": 1, "ETag": "etag1"},
      {"PartNumber": 2, "ETag": "etag2"}
    ],
    "file_id": "uuid...",
    "filename": "large-evidence.zip"
  }'
```

## 💻 **Frontend Integration**

### JavaScript Example:
```javascript
import LargeFileUploader from './large-file-upload-example.js';

const uploader = new LargeFileUploader();

// Upload 50GB file
const result = await uploader.uploadLargeFile(file, {
    case_id: 'CASE-001',
    description: 'Large forensic dataset'
});
```

### Features:
- **Progress tracking**: Real-time upload progress
- **Parallel uploads**: 3 chunks upload simultaneously  
- **Retry logic**: Automatic retry with exponential backoff
- **Error handling**: Graceful failure with cleanup
- **Resume capability**: Can be extended to resume failed uploads

## 🔧 **Performance Optimizations**

### 1. **Network Optimizations**
- **Concurrent uploads**: 3 chunks in parallel
- **Chunk size**: 100MB optimal for most connections
- **Retry logic**: Handles temporary network issues
- **Connection pooling**: Reuses HTTP connections

### 2. **Memory Management**
- **Streaming**: Processes file in chunks, not all at once
- **Garbage collection**: Releases chunk memory after upload
- **Browser limits**: Works within browser memory constraints

### 3. **Error Recovery**
- **Chunk-level retries**: Only retry failed chunks
- **Automatic cleanup**: Aborts incomplete uploads
- **Exponential backoff**: Reduces server load on retries

## 🛡️ **Security & Reliability**

### Security:
- **Pre-signed URLs**: No AWS credentials in frontend
- **Time-limited URLs**: 1-hour expiration per chunk
- **Content validation**: File type and size validation
- **Clean filenames**: Sanitized for S3 compatibility

### Reliability:
- **Atomic operations**: Upload either succeeds or fails completely
- **Orphan prevention**: Automatic cleanup of failed uploads
- **Progress persistence**: Can be extended to save progress
- **Network resilience**: Handles connection drops gracefully

## 📈 **Monitoring & Debugging**

### Logs to Watch:
```bash
# Backend logs show multipart operations
127.0.0.1 - - [19/Aug/2025 15:19:33] "POST /api/multipart-upload/initiate HTTP/1.1" 200 -
127.0.0.1 - - [19/Aug/2025 15:19:34] "POST /api/multipart-upload/chunk HTTP/1.1" 200 -
127.0.0.1 - - [19/Aug/2025 15:19:35] "POST /api/multipart-upload/complete HTTP/1.1" 200 -
```

### Frontend Console:
```
Starting upload of large-evidence.zip (50.0 GB)
Initiated multipart upload: 512 chunks of 100.0 MB
Progress: 1.0% (5/512 chunks)
Progress: 2.0% (10/512 chunks)
...
✅ Large file upload completed successfully!
```

## 🚨 **Important Considerations**

### 1. **AWS Costs**
- Multipart uploads have per-request costs
- 512 chunks = 512 PUT requests for 50GB file
- Consider chunk size vs. cost trade-offs

### 2. **Browser Limitations**
- File API memory limits vary by browser
- Large files may require additional optimization
- Consider Web Workers for heavy processing

### 3. **Network Requirements**
- Stable internet connection recommended
- Upload time: ~2-4 hours for 50GB (depending on speed)
- Consider resumable uploads for unreliable connections

### 4. **S3 Configuration**
- Ensure bucket has multipart upload permissions
- Set appropriate CORS policies
- Monitor S3 storage costs

## 🔄 **Future Enhancements**

### Possible Improvements:
1. **Resume uploads**: Save progress and resume interrupted uploads
2. **Compression**: Compress chunks before upload
3. **Deduplication**: Skip uploading duplicate chunks
4. **Background uploads**: Upload in service worker
5. **Upload scheduling**: Queue large uploads for off-peak hours

## ✅ **Testing the System**

### Test with curl:
```bash
# Test 5GB file upload initiation
curl -X POST http://localhost:5001/api/multipart-upload/initiate \
  -H "Content-Type: application/json" \
  -d '{"filename": "test-5gb.zip", "file_size": 5368709120, "file_type": "application/zip"}'
```

### Expected Response:
```json
{
  "chunk_size": 104857600,
  "file_id": "uuid...",
  "s3_key": "jim-ai-uploads/20250819_151933_test-5gb.zip",
  "total_chunks": 52,
  "upload_id": "multipart-upload-id..."
}
```

The system is now ready to handle your 50-100GB forensic files! 🚀

