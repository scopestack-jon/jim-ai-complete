#!/usr/bin/env python3
"""
Large Cell Phone Data Processor for JIM AI
Handles 150GB+ forensic extractions with chunked upload and processing
"""

import os
import sys
import boto3
import hashlib
import sqlite3
import json
import csv
import zipfile
import tarfile
import time
from datetime import datetime
from pathlib import Path
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

class LargeDataProcessor:
    def __init__(self):
        self.s3_client = boto3.client('s3', region_name='us-east-1')
        self.bedrock_client = boto3.client('bedrock-agent', region_name='us-east-1')
        self.bucket = "jim-ai-forensic-data-1758988022"
        self.kb_id = "HFCMSKWHFU"
        self.data_source_id = "CZJWLDWEFD"
        self.chunk_size = 50 * 1024 * 1024  # 50MB chunks for Knowledge Base
        self.upload_threads = 5  # Parallel uploads

    def calculate_checksum(self, file_path):
        """Calculate SHA256 checksum"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    def extract_sqlite_to_csv(self, sqlite_path, output_dir):
        """Convert SQLite databases to CSV files"""
        try:
            conn = sqlite3.connect(sqlite_path)
            cursor = conn.cursor()

            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()

            extracted_files = []

            for table in tables:
                table_name = table[0]
                if table_name.startswith('sqlite_'):
                    continue

                try:
                    # Export table to CSV
                    cursor.execute(f"SELECT * FROM {table_name}")
                    rows = cursor.fetchall()

                    if rows:
                        # Get column names
                        cursor.execute(f"PRAGMA table_info({table_name})")
                        columns = [col[1] for col in cursor.fetchall()]

                        # Write CSV
                        csv_path = os.path.join(output_dir, f"{table_name}.csv")
                        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                            writer = csv.writer(csvfile)
                            writer.writerow(columns)
                            writer.writerows(rows)

                        extracted_files.append(csv_path)
                        print(f"Extracted {table_name}: {len(rows)} records")

                except Exception as e:
                    print(f"Warning: Could not extract table {table_name}: {e}")
                    continue

            conn.close()
            return extracted_files

        except Exception as e:
            print(f"Error processing SQLite file {sqlite_path}: {e}")
            return []

    def extract_archive(self, archive_path, extract_dir):
        """Extract ZIP/TAR archives"""
        extracted_files = []

        try:
            if archive_path.lower().endswith('.zip'):
                with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
                    extracted_files = [os.path.join(extract_dir, name) for name in zip_ref.namelist()]

            elif archive_path.lower().endswith(('.tar', '.tar.gz', '.tgz')):
                with tarfile.open(archive_path, 'r:*') as tar_ref:
                    tar_ref.extractall(extract_dir)
                    extracted_files = [os.path.join(extract_dir, member.name) for member in tar_ref.getmembers() if member.isfile()]

            print(f"Extracted {len(extracted_files)} files from {os.path.basename(archive_path)}")
            return extracted_files

        except Exception as e:
            print(f"Error extracting {archive_path}: {e}")
            return []

    def split_large_file(self, file_path, output_dir):
        """Split large files into Knowledge Base compatible chunks"""
        file_size = os.path.getsize(file_path)

        if file_size <= self.chunk_size:
            return [file_path]

        chunks = []
        filename = os.path.basename(file_path)
        name, ext = os.path.splitext(filename)

        print(f"Splitting large file: {filename} ({file_size / 1024 / 1024:.1f}MB)")

        with open(file_path, 'rb') as f:
            chunk_num = 1
            while True:
                chunk_data = f.read(self.chunk_size)
                if not chunk_data:
                    break

                chunk_filename = f"{name}_part{chunk_num:03d}{ext}"
                chunk_path = os.path.join(output_dir, chunk_filename)

                with open(chunk_path, 'wb') as chunk_file:
                    chunk_file.write(chunk_data)

                chunks.append(chunk_path)
                chunk_num += 1

                if chunk_num % 10 == 0:
                    print(f"  Created {chunk_num-1} chunks...")

        print(f"Split into {len(chunks)} chunks")
        return chunks

    def upload_file_to_s3(self, file_path, s3_key):
        """Upload single file to S3 with retry logic"""
        max_retries = 3

        for attempt in range(max_retries):
            try:
                file_size = os.path.getsize(file_path)
                print(f"Uploading {os.path.basename(file_path)} ({file_size / 1024 / 1024:.1f}MB)")

                # Use multipart upload for large files
                if file_size > 100 * 1024 * 1024:  # 100MB
                    self.s3_client.upload_file(
                        file_path,
                        self.bucket,
                        s3_key,
                        Config=boto3.s3.transfer.TransferConfig(
                            multipart_threshold=1024 * 25,  # 25MB
                            max_concurrency=10,
                            multipart_chunksize=1024 * 25,
                            use_threads=True
                        )
                    )
                else:
                    self.s3_client.upload_file(file_path, self.bucket, s3_key)

                return True

            except Exception as e:
                print(f"Upload attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    print(f"Failed to upload {file_path} after {max_retries} attempts")
                    return False

    def process_large_extraction(self, data_directory):
        """Process entire cell phone extraction directory"""
        print(f"🔍 Processing large cell phone extraction: {data_directory}")
        print(f"📊 Scanning directory structure...")

        # Create processing directories
        work_dir = "/tmp/claude/large_processing"
        os.makedirs(work_dir, exist_ok=True)

        processed_files = []
        upload_tasks = []

        # Walk through all files
        for root, dirs, files in os.walk(data_directory):
            for file in files:
                file_path = os.path.join(root, file)
                file_size = os.path.getsize(file_path)

                print(f"Processing: {file} ({file_size / 1024 / 1024:.1f}MB)")

                # Skip very small files
                if file_size < 1024:  # Skip files smaller than 1KB
                    continue

                try:
                    # Handle different file types
                    if file.lower().endswith(('.db', '.sqlite', '.sqlite3')):
                        # Convert SQLite to CSV
                        csv_files = self.extract_sqlite_to_csv(file_path, work_dir)
                        processed_files.extend(csv_files)

                    elif file.lower().endswith(('.zip', '.tar', '.tar.gz', '.tgz')):
                        # Extract archives
                        extract_dir = os.path.join(work_dir, f"extracted_{os.path.basename(file)}")
                        os.makedirs(extract_dir, exist_ok=True)
                        extracted_files = self.extract_archive(file_path, extract_dir)

                        # Process extracted files recursively
                        for extracted_file in extracted_files:
                            if os.path.getsize(extracted_file) > 1024:
                                processed_files.append(extracted_file)

                    else:
                        # Regular files - check if they need splitting
                        if file_size > self.chunk_size:
                            chunks = self.split_large_file(file_path, work_dir)
                            processed_files.extend(chunks)
                        else:
                            processed_files.append(file_path)

                except Exception as e:
                    print(f"Error processing {file}: {e}")
                    continue

        print(f"📦 Total files to upload: {len(processed_files)}")

        # Upload files in parallel
        uploaded_count = 0
        failed_count = 0

        with ThreadPoolExecutor(max_workers=self.upload_threads) as executor:
            # Submit upload tasks
            future_to_file = {}

            for file_path in processed_files:
                filename = os.path.basename(file_path)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                s3_key = f"kb/{timestamp}_{filename}"

                future = executor.submit(self.upload_file_to_s3, file_path, s3_key)
                future_to_file[future] = file_path

            # Process completed uploads
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    success = future.result()
                    if success:
                        uploaded_count += 1
                        print(f"✅ Uploaded {uploaded_count}/{len(processed_files)}: {os.path.basename(file_path)}")
                    else:
                        failed_count += 1
                        print(f"❌ Failed {failed_count}: {os.path.basename(file_path)}")
                except Exception as e:
                    failed_count += 1
                    print(f"❌ Exception uploading {os.path.basename(file_path)}: {e}")

        # Clean up temporary files
        print("🧹 Cleaning up temporary files...")
        for file_path in processed_files:
            if file_path.startswith(work_dir):
                try:
                    os.remove(file_path)
                except:
                    pass

        print(f"📊 Upload Summary:")
        print(f"   ✅ Successful: {uploaded_count}")
        print(f"   ❌ Failed: {failed_count}")
        print(f"   📈 Success rate: {uploaded_count/(uploaded_count+failed_count)*100:.1f}%")

        # Start Knowledge Base ingestion
        if uploaded_count > 0:
            print("🚀 Starting Knowledge Base ingestion...")
            try:
                response = self.bedrock_client.start_ingestion_job(
                    knowledgeBaseId=self.kb_id,
                    dataSourceId=self.data_source_id
                )
                job_id = response['ingestionJob']['ingestionJobId']
                print(f"✅ Ingestion job started: {job_id}")
                print("⏳ Processing will take 15-45 minutes for large datasets")
                return job_id
            except Exception as e:
                print(f"❌ Failed to start ingestion job: {e}")
                return None

        return None

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 large-data-processor.py /path/to/cell-phone-extraction")
        print("\nExample:")
        print("  python3 large-data-processor.py /Volumes/Evidence/iPhone_Extraction")
        print("  python3 large-data-processor.py /home/analyst/case123/android_data")
        return

    data_directory = sys.argv[1]

    if not os.path.exists(data_directory):
        print(f"Error: Directory not found: {data_directory}")
        return

    processor = LargeDataProcessor()

    print("🚀 JIM AI Large Data Processor")
    print("=" * 50)
    print(f"📂 Source: {data_directory}")
    print(f"☁️  Target: s3://{processor.bucket}/kb/")
    print(f"🧠 Knowledge Base: {processor.kb_id}")
    print("=" * 50)

    start_time = time.time()
    job_id = processor.process_large_extraction(data_directory)
    end_time = time.time()

    print("=" * 50)
    print(f"⏱️  Processing time: {end_time - start_time:.1f} seconds")

    if job_id:
        print(f"🎯 Next steps:")
        print(f"   1. Monitor ingestion job: {job_id}")
        print(f"   2. Open web interface: http://localhost:8080")
        print(f"   3. Wait 15-45 minutes for processing to complete")
        print(f"   4. Start querying your cell phone data!")
    else:
        print("❌ No files were successfully uploaded")

if __name__ == "__main__":
    main()