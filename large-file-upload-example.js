/**
 * Large File Upload Example - 50-100GB Support
 * This demonstrates how to upload very large files using multipart uploads
 */

class LargeFileUploader {
    constructor() {
        this.chunkSize = 100 * 1024 * 1024; // 100MB chunks
        this.maxConcurrentUploads = 3; // Upload 3 chunks simultaneously
        this.retryAttempts = 3;
    }

    async uploadLargeFile(file, metadata = {}) {
        console.log(`Starting upload of ${file.name} (${this.formatBytes(file.size)})`);
        
        try {
            // Step 1: Check if file needs multipart upload
            const config = await this.getConfig();
            const useMultipart = file.size > config.multipart_threshold;
            
            if (!useMultipart) {
                return await this.uploadSmallFile(file, metadata);
            }

            // Step 2: Initiate multipart upload
            const initResponse = await this.initiateMultipartUpload(file, metadata);
            const { upload_id, s3_key, chunk_size, total_chunks, file_id } = initResponse;
            
            console.log(`Initiated multipart upload: ${total_chunks} chunks of ${this.formatBytes(chunk_size)}`);
            
            // Step 3: Upload chunks in parallel with progress tracking
            const parts = await this.uploadChunks(file, {
                upload_id,
                s3_key,
                chunk_size,
                total_chunks
            });
            
            // Step 4: Complete multipart upload
            const completeResponse = await this.completeMultipartUpload({
                upload_id,
                s3_key,
                parts,
                file_id,
                filename: file.name,
                file_size: file.size,
                file_type: file.type,
                ...metadata
            });
            
            console.log('✅ Large file upload completed successfully!');
            return completeResponse;
            
        } catch (error) {
            console.error('❌ Large file upload failed:', error);
            // Attempt to abort the upload to clean up
            if (error.upload_id && error.s3_key) {
                await this.abortMultipartUpload(error.upload_id, error.s3_key);
            }
            throw error;
        }
    }

    async getConfig() {
        const response = await fetch('/api/config');
        return await response.json();
    }

    async initiateMultipartUpload(file, metadata) {
        const response = await fetch('/api/multipart-upload/initiate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                filename: file.name,
                file_size: file.size,
                file_type: file.type,
                case_id: metadata.case_id || '',
                description: metadata.description || ''
            })
        });
        
        if (!response.ok) {
            throw new Error(`Failed to initiate upload: ${response.statusText}`);
        }
        
        return await response.json();
    }

    async uploadChunks(file, { upload_id, s3_key, chunk_size, total_chunks }) {
        const parts = [];
        const uploadPromises = [];
        let uploadedChunks = 0;
        
        // Create chunks and upload with concurrency control
        for (let i = 0; i < total_chunks; i++) {
            const partNumber = i + 1;
            const start = i * chunk_size;
            const end = Math.min(start + chunk_size, file.size);
            const chunk = file.slice(start, end);
            
            // Control concurrency
            if (uploadPromises.length >= this.maxConcurrentUploads) {
                await Promise.race(uploadPromises);
            }
            
            const uploadPromise = this.uploadChunk(chunk, {
                upload_id,
                s3_key,
                part_number: partNumber
            }).then((result) => {
                parts.push(result);
                uploadedChunks++;
                
                // Update progress
                const progress = (uploadedChunks / total_chunks) * 100;
                console.log(`Progress: ${progress.toFixed(1)}% (${uploadedChunks}/${total_chunks} chunks)`);
                
                // Remove from active uploads
                const index = uploadPromises.indexOf(uploadPromise);
                if (index > -1) uploadPromises.splice(index, 1);
                
                return result;
            }).catch((error) => {
                console.error(`Failed to upload chunk ${partNumber}:`, error);
                throw error;
            });
            
            uploadPromises.push(uploadPromise);
        }
        
        // Wait for all uploads to complete
        await Promise.all(uploadPromises);
        
        // Sort parts by part number
        parts.sort((a, b) => a.PartNumber - b.PartNumber);
        
        return parts;
    }

    async uploadChunk(chunk, { upload_id, s3_key, part_number }) {
        // Get pre-signed URL for this chunk
        const urlResponse = await fetch('/api/multipart-upload/chunk', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ upload_id, s3_key, part_number })
        });
        
        if (!urlResponse.ok) {
            throw new Error(`Failed to get chunk upload URL: ${urlResponse.statusText}`);
        }
        
        const { upload_url } = await urlResponse.json();
        
        // Upload chunk with retry logic
        let attempt = 0;
        while (attempt < this.retryAttempts) {
            try {
                const uploadResponse = await fetch(upload_url, {
                    method: 'PUT',
                    body: chunk,
                    headers: {
                        'Content-Type': 'application/octet-stream'
                    }
                });
                
                if (!uploadResponse.ok) {
                    throw new Error(`Chunk upload failed: ${uploadResponse.statusText}`);
                }
                
                // Get ETag from response headers
                const etag = uploadResponse.headers.get('ETag');
                if (!etag) {
                    throw new Error('No ETag received from S3');
                }
                
                return {
                    PartNumber: part_number,
                    ETag: etag
                };
                
            } catch (error) {
                attempt++;
                if (attempt >= this.retryAttempts) {
                    throw error;
                }
                
                console.warn(`Retrying chunk ${part_number} upload (attempt ${attempt + 1})`);
                await this.delay(1000 * attempt); // Exponential backoff
            }
        }
    }

    async completeMultipartUpload(data) {
        const response = await fetch('/api/multipart-upload/complete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            throw new Error(`Failed to complete upload: ${response.statusText}`);
        }
        
        return await response.json();
    }

    async abortMultipartUpload(upload_id, s3_key) {
        try {
            await fetch('/api/multipart-upload/abort', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ upload_id, s3_key })
            });
            console.log('🧹 Multipart upload aborted and cleaned up');
        } catch (error) {
            console.error('Failed to abort multipart upload:', error);
        }
    }

    async uploadSmallFile(file, metadata) {
        // Use existing single-part upload for files < 1GB
        console.log('Using single-part upload for small file');
        // ... existing upload logic
    }

    formatBytes(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Usage Example:
/*
const uploader = new LargeFileUploader();

// Handle file selection
document.getElementById('fileInput').addEventListener('change', async (event) => {
    const file = event.target.files[0];
    if (!file) return;
    
    try {
        const result = await uploader.uploadLargeFile(file, {
            case_id: 'CASE-001',
            description: 'Large forensic evidence file'
        });
        
        console.log('Upload successful:', result);
    } catch (error) {
        console.error('Upload failed:', error);
    }
});
*/

export default LargeFileUploader;

