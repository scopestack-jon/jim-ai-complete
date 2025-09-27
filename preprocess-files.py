#!/usr/bin/env python3
"""
Preprocessor for large forensic files
Splits files into ≤50MB chunks for Bedrock Knowledge Base ingestion
"""

import os
import sys
import boto3
import hashlib
import zipfile
import tarfile
import mimetypes
from pathlib import Path
from typing import List, Tuple
import json
from datetime import datetime

# Load configuration
BUCKET_NAME = "jim-ai-forensic-data-1758988022"
RAW_PREFIX = "raw/"
KB_PREFIX = "kb/"
MAX_SIZE_MB = 50
MAX_SIZE_BYTES = MAX_SIZE_MB * 1024 * 1024

s3_client = boto3.client('s3', region_name='us-east-1')

def get_file_type(file_path: str) -> str:
    """Determine file type for proper processing"""
    mime_type, _ = mimetypes.guess_type(file_path)

    # Map MIME types to Bedrock-supported formats
    supported_types = {
        'application/pdf': 'pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
        'application/msword': 'doc',
        'text/plain': 'txt',
        'text/csv': 'csv',
        'text/html': 'html',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'xlsx',
        'application/vnd.ms-excel': 'xls',
        'application/json': 'json'
    }

    for mime, ext in supported_types.items():
        if mime_type and mime_type.startswith(mime.split('/')[0]):
            return ext

    # Default to txt for unknown text types
    return 'txt'

def extract_archive(file_path: str, extract_dir: str) -> List[str]:
    """Extract archive files (zip, tar, etc.)"""
    extracted_files = []

    if zipfile.is_zipfile(file_path):
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
            extracted_files = [os.path.join(extract_dir, name) for name in zip_ref.namelist()]

    elif tarfile.is_tarfile(file_path):
        with tarfile.open(file_path, 'r:*') as tar_ref:
            tar_ref.extractall(extract_dir)
            extracted_files = [os.path.join(extract_dir, member.name) for member in tar_ref.getmembers()]

    return extracted_files

def split_large_file(file_path: str, output_dir: str) -> List[Tuple[str, str]]:
    """Split large files into chunks ≤50MB"""
    file_size = os.path.getsize(file_path)
    chunks = []

    if file_size <= MAX_SIZE_BYTES:
        # File is already small enough
        return [(file_path, os.path.basename(file_path))]

    # Split file into chunks
    base_name = os.path.basename(file_path)
    name_without_ext = os.path.splitext(base_name)[0]
    extension = os.path.splitext(base_name)[1]

    with open(file_path, 'rb') as f:
        chunk_num = 1
        while True:
            chunk_data = f.read(MAX_SIZE_BYTES)
            if not chunk_data:
                break

            chunk_name = f"{name_without_ext}_part{chunk_num:03d}{extension}"
            chunk_path = os.path.join(output_dir, chunk_name)

            with open(chunk_path, 'wb') as chunk_file:
                chunk_file.write(chunk_data)

            chunks.append((chunk_path, chunk_name))
            chunk_num += 1

    return chunks

def calculate_checksum(file_path: str) -> str:
    """Calculate SHA256 checksum for integrity verification"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def process_file(local_file_path: str, s3_raw_key: str) -> dict:
    """Process a single file for Knowledge Base ingestion"""
    print(f"Processing: {local_file_path}")

    # Create processing directory
    process_dir = f"/tmp/jim-process-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    os.makedirs(process_dir, exist_ok=True)

    results = {
        'original_file': local_file_path,
        's3_raw_key': s3_raw_key,
        'processed_files': [],
        'metadata': {}
    }

    # Calculate checksum
    checksum = calculate_checksum(local_file_path)
    results['metadata']['checksum'] = checksum
    results['metadata']['original_size'] = os.path.getsize(local_file_path)

    # Check if it's an archive
    if local_file_path.endswith(('.zip', '.tar', '.tar.gz', '.tgz')):
        print(f"  Extracting archive...")
        extracted = extract_archive(local_file_path, process_dir)
        files_to_process = extracted
    else:
        files_to_process = [local_file_path]

    # Process each file
    for file_to_process in files_to_process:
        if not os.path.isfile(file_to_process):
            continue

        file_type = get_file_type(file_to_process)

        # Only process supported file types
        if file_type in ['pdf', 'docx', 'doc', 'txt', 'csv', 'html', 'xlsx', 'xls', 'json']:
            chunks = split_large_file(file_to_process, process_dir)

            for chunk_path, chunk_name in chunks:
                # Upload to S3 KB prefix
                s3_kb_key = f"{KB_PREFIX}{chunk_name}"

                print(f"  Uploading chunk: {chunk_name} -> s3://{BUCKET_NAME}/{s3_kb_key}")

                with open(chunk_path, 'rb') as chunk_file:
                    s3_client.put_object(
                        Bucket=BUCKET_NAME,
                        Key=s3_kb_key,
                        Body=chunk_file,
                        Metadata={
                            'original-file': os.path.basename(local_file_path),
                            'checksum': checksum,
                            'file-type': file_type
                        }
                    )

                results['processed_files'].append({
                    'local_path': chunk_path,
                    's3_key': s3_kb_key,
                    'size': os.path.getsize(chunk_path),
                    'type': file_type
                })

    # Clean up temp files
    for file in os.listdir(process_dir):
        os.remove(os.path.join(process_dir, file))
    os.rmdir(process_dir)

    return results

def upload_raw_file(local_file_path: str) -> str:
    """Upload original file to S3 raw prefix"""
    file_name = os.path.basename(local_file_path)
    s3_key = f"{RAW_PREFIX}{file_name}"

    print(f"Uploading raw file: {file_name} -> s3://{BUCKET_NAME}/{s3_key}")

    # Use multipart upload for large files
    file_size = os.path.getsize(local_file_path)

    if file_size > 100 * 1024 * 1024:  # 100MB
        print(f"  Using multipart upload for large file ({file_size / 1024 / 1024:.1f} MB)")

    with open(local_file_path, 'rb') as f:
        s3_client.upload_fileobj(
            f,
            BUCKET_NAME,
            s3_key,
            Config=boto3.s3.transfer.TransferConfig(
                multipart_threshold=1024 * 64,  # 64MB
                max_concurrency=10,
                multipart_chunksize=1024 * 64,
                use_threads=True
            )
        )

    return s3_key

def process_directory(directory_path: str):
    """Process all files in a directory"""
    manifest = {
        'process_time': datetime.now().isoformat(),
        'directory': directory_path,
        'files': []
    }

    for root, dirs, files in os.walk(directory_path):
        for file in files:
            file_path = os.path.join(root, file)

            # Skip hidden files and system files
            if file.startswith('.'):
                continue

            try:
                # Upload raw file
                s3_raw_key = upload_raw_file(file_path)

                # Process for KB
                result = process_file(file_path, s3_raw_key)
                manifest['files'].append(result)

            except Exception as e:
                print(f"Error processing {file_path}: {str(e)}")
                manifest['files'].append({
                    'file': file_path,
                    'error': str(e)
                })

    # Save manifest
    manifest_path = f"process_manifest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)

    print(f"\nProcessing complete. Manifest saved to: {manifest_path}")

    # Upload manifest to S3
    s3_client.put_object(
        Bucket=BUCKET_NAME,
        Key=f"manifests/{manifest_path}",
        Body=json.dumps(manifest, indent=2),
        ContentType='application/json'
    )

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python preprocess-files.py <file_or_directory>")
        print("\nThis script will:")
        print("1. Upload original files to s3://bucket/raw/")
        print("2. Extract archives if needed")
        print("3. Split large files into ≤50MB chunks")
        print("4. Upload processed files to s3://bucket/kb/")
        sys.exit(1)

    path = sys.argv[1]

    if os.path.isdir(path):
        process_directory(path)
    elif os.path.isfile(path):
        s3_raw_key = upload_raw_file(path)
        result = process_file(path, s3_raw_key)
        print(json.dumps(result, indent=2))
    else:
        print(f"Error: {path} is not a valid file or directory")
        sys.exit(1)