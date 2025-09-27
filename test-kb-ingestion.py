#!/usr/bin/env python3
"""
Test Knowledge Base ingestion with sample documents
"""

import boto3
import json
import time
import os

def create_test_documents():
    """Create sample forensic documents for testing"""

    test_docs = [
        {
            "filename": "case-summary.txt",
            "content": """
Case Summary: Digital Forensics Investigation
Case Number: JIM-2024-001
Date: September 27, 2024

OVERVIEW:
This case involves the forensic analysis of digital evidence collected from a corporate security incident.
The investigation focuses on unauthorized access to sensitive financial data.

KEY FINDINGS:
- Suspicious login activities detected between 2:00 AM - 4:00 AM
- Multiple failed authentication attempts from external IP addresses
- Unusual file access patterns in the accounting database
- Evidence of data exfiltration via encrypted channels

EVIDENCE COLLECTED:
1. Server access logs (500MB)
2. Network traffic captures (2.1GB)
3. Database audit trails (150MB)
4. Email communications (75MB)

TIMELINE:
- September 15: Initial breach detected
- September 16: Systems isolated and forensic imaging began
- September 18: Analysis of network traffic completed
- September 20: Database audit review finished
- September 22: Final report compilation

RECOMMENDATIONS:
- Implement multi-factor authentication
- Enhanced monitoring of after-hours access
- Regular security audits of database access
- Employee security awareness training
            """
        },
        {
            "filename": "evidence-log.txt",
            "content": """
EVIDENCE LOG - Case JIM-2024-001

Item #001
Description: Primary server hard drive
Serial Number: WD-WCAV12345678
Size: 1TB Western Digital
Chain of Custody: Collected by Agent Smith on 09/16/2024
Location: Evidence locker A-15
Hash: SHA256: a1b2c3d4e5f6789012345678901234567890abcdef

Item #002
Description: Network router configuration backup
File: router_config_backup_20240915.txt
Size: 2.5MB
Collected: 09/16/2024 15:30
Hash: MD5: 9876543210abcdef1234567890123456

Item #003
Description: Employee workstation memory dump
Source: Finance Dept. Computer #7
Size: 16GB RAM dump
Format: .mem file
Collected: 09/17/2024 09:15
Analyst: Detective Johnson
Hash: SHA1: fedcba0987654321fedcba0987654321fedcba09

Item #004
Description: Email server logs
Date Range: 09/10/2024 - 09/20/2024
Size: 250MB compressed
Format: .mbox export
Chain of Custody: IT Admin -> Legal -> Forensics
Processing Status: Completed - No encrypted emails found
            """
        },
        {
            "filename": "technical-analysis.txt",
            "content": """
TECHNICAL ANALYSIS REPORT
Case: JIM-2024-001
Analyst: Dr. Sarah Chen, CISSP
Date: September 25, 2024

MALWARE ANALYSIS:
No malicious software detected on primary systems. However, analysis revealed:
- Suspicious PowerShell scripts in temp directories
- Modified registry entries related to network settings
- Unusual scheduled tasks created during incident timeframe

NETWORK FORENSICS:
Traffic analysis indicates:
- 47 GB of data transferred to external IP 203.45.67.89
- Connection established via TOR network
- Data transmitted in 50MB chunks over 3-day period
- Encryption used: AES-256 with custom key derivation

FILE SYSTEM ANALYSIS:
Key findings from disk forensics:
- 1,247 deleted files recovered from unallocated space
- File timestamps show systematic deletion on 09/15/2024
- Browser history cleared but partial cache recovered
- Financial spreadsheets accessed outside normal business hours

DATABASE ANALYSIS:
Query log examination reveals:
- 15,000 customer records accessed via admin account
- Bulk export operations not matching normal usage patterns
- Database backup created and immediately deleted
- Foreign key constraints bypassed in 12 instances

MEMORY ANALYSIS:
RAM dump processing identified:
- Credential harvesting tools loaded in memory
- Network connection artifacts to C&C servers
- Encryption keys for data exfiltration tools
- Evidence of anti-forensics techniques

CONCLUSION:
Sophisticated insider threat with advanced technical knowledge.
Recommend immediate password resets and privilege review.
            """
        }
    ]

    # Create test directory
    test_dir = "/tmp/jim-test-docs"
    os.makedirs(test_dir, exist_ok=True)

    created_files = []
    for doc in test_docs:
        file_path = os.path.join(test_dir, doc["filename"])
        with open(file_path, 'w') as f:
            f.write(doc["content"])
        created_files.append(file_path)
        print(f"Created: {file_path}")

    return created_files

def upload_to_s3(files, bucket_name):
    """Upload test files to S3 KB prefix"""
    s3_client = boto3.client('s3', region_name='us-east-1')

    uploaded_keys = []
    for file_path in files:
        filename = os.path.basename(file_path)
        s3_key = f"kb/{filename}"

        print(f"Uploading {filename} to s3://{bucket_name}/{s3_key}")

        with open(file_path, 'rb') as f:
            s3_client.put_object(
                Bucket=bucket_name,
                Key=s3_key,
                Body=f,
                ContentType='text/plain',
                Metadata={
                    'source': 'test-documents',
                    'case': 'JIM-2024-001'
                }
            )
        uploaded_keys.append(s3_key)

    return uploaded_keys

def start_ingestion(kb_id, data_source_id):
    """Start Knowledge Base ingestion job"""
    bedrock_client = boto3.client('bedrock-agent', region_name='us-east-1')

    try:
        response = bedrock_client.start_ingestion_job(
            knowledgeBaseId=kb_id,
            dataSourceId=data_source_id,
            description="Test ingestion of forensic case documents"
        )

        job_id = response['ingestionJob']['ingestionJobId']
        print(f"Ingestion job started: {job_id}")
        return job_id

    except Exception as e:
        print(f"Error starting ingestion: {e}")
        return None

def check_ingestion_status(kb_id, data_source_id, job_id):
    """Check ingestion job status"""
    bedrock_client = boto3.client('bedrock-agent', region_name='us-east-1')

    try:
        response = bedrock_client.get_ingestion_job(
            knowledgeBaseId=kb_id,
            dataSourceId=data_source_id,
            ingestionJobId=job_id
        )

        status = response['ingestionJob']['status']
        print(f"Ingestion status: {status}")

        if 'statistics' in response['ingestionJob']:
            stats = response['ingestionJob']['statistics']
            print(f"Documents processed: {stats.get('numberOfDocumentsScanned', 0)}")
            print(f"Documents indexed: {stats.get('numberOfDocumentsIndexed', 0)}")

        return status

    except Exception as e:
        print(f"Error checking status: {e}")
        return None

if __name__ == "__main__":
    print("Creating test forensic documents...")

    # Configuration
    BUCKET_NAME = "jim-ai-forensic-data-1758988022"

    # Use the final Knowledge Base configuration
    KB_ID = "HFCMSKWHFU"
    DATA_SOURCE_ID = "CZJWLDWEFD"

    # Create and upload test documents
    files = create_test_documents()
    uploaded_keys = upload_to_s3(files, BUCKET_NAME)

    print(f"\nUploaded {len(uploaded_keys)} files to S3:")
    for key in uploaded_keys:
        print(f"  s3://{BUCKET_NAME}/{key}")

    # Start ingestion
    print(f"\nStarting ingestion job...")
    job_id = start_ingestion(KB_ID, DATA_SOURCE_ID)

    if job_id:
        print(f"\nMonitoring ingestion progress...")
        while True:
            status = check_ingestion_status(KB_ID, DATA_SOURCE_ID, job_id)
            if status in ['COMPLETE', 'FAILED']:
                break
            time.sleep(10)

        if status == 'COMPLETE':
            print("\n✅ Ingestion completed successfully!")
            print("You can now test queries against the Knowledge Base")
        else:
            print("\n❌ Ingestion failed. Check CloudWatch logs for details.")

    # Clean up local test files
    for file_path in files:
        os.remove(file_path)
    os.rmdir("/tmp/jim-test-docs")
    print("\nLocal test files cleaned up")