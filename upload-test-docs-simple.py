#!/usr/bin/env python3
"""
Upload test documents without encryption for Knowledge Base testing
"""

import boto3
import os

def upload_simple_test_docs():
    """Upload test documents without KMS encryption"""

    s3_client = boto3.client('s3', region_name='us-east-1')
    bucket_name = "jim-ai-forensic-data-1758988022"

    # Create simple test documents
    test_docs = {
        "case001-summary.txt": """Case Summary - JIM-2024-001
Investigation Type: Digital Forensics
Incident Date: September 15, 2024

OVERVIEW:
Corporate security incident involving unauthorized access to financial databases.
Suspect: Internal employee with database administrator privileges.

KEY FINDINGS:
- Unauthorized access occurred between 2 AM - 4 AM on September 15
- 15,000 customer records accessed via admin account
- Data exfiltration tools found on suspect workstation
- Network traffic shows 47 GB transferred to external IP

EVIDENCE:
- Server logs showing suspicious queries
- Memory dump from suspect workstation
- Network packet captures
- Email communications""",

        "evidence-inventory.txt": """EVIDENCE INVENTORY - Case JIM-2024-001

Item 001: Primary Database Server
- Description: Dell PowerEdge R740 server
- Serial: ABC123456789
- Chain of Custody: Collected by Agent Johnson 09/16/2024
- Status: Forensic image created
- Hash: SHA256:a1b2c3d4e5f6...

Item 002: Suspect Workstation
- Description: Dell Optiplex 7090
- User: database_admin_user
- Collection Date: 09/16/2024 10:30 AM
- Analysis Status: Memory dump completed
- Key Findings: Data exfiltration tools installed

Item 003: Network Router Logs
- Type: Cisco ASA 5516-X logs
- Date Range: 09/10/2024 - 09/20/2024
- Size: 2.3 GB compressed
- Analysis: Shows suspicious outbound connections""",

        "technical-findings.txt": """TECHNICAL ANALYSIS REPORT
Case: JIM-2024-001
Analyst: Dr. Sarah Chen
Date: September 25, 2024

MALWARE ANALYSIS:
Custom data exfiltration tool detected:
- Filename: backup_utility.exe
- MD5: d41d8cd98f00b204e9800998ecf8427e
- Purpose: Database query automation and encryption

NETWORK FORENSICS:
Suspicious network activity identified:
- Destination IP: 203.45.67.89 (TOR exit node)
- Protocol: HTTPS over TOR
- Data volume: 47.2 GB transferred
- Time frame: 3 consecutive nights

DATABASE FORENSICS:
Unauthorized queries detected:
- SELECT statements on customer_data table
- Bulk export operations outside normal hours
- Privilege escalation attempts logged
- Foreign key constraints bypassed

TIMELINE:
- Sept 10: Initial reconnaissance
- Sept 12: Tool installation
- Sept 14: Permission testing
- Sept 15: Data exfiltration begins
- Sept 16: Discovery and containment"""
    }

    print("Uploading test documents without encryption...")

    for filename, content in test_docs.items():
        s3_key = f"kb/{filename}"

        print(f"Uploading: {filename}")

        # Upload without server-side encryption
        s3_client.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=content.encode('utf-8'),
            ContentType='text/plain',
            Metadata={
                'case': 'JIM-2024-001',
                'source': 'test-data',
                'type': 'forensic-document'
            }
        )

        print(f"  Uploaded to: s3://{bucket_name}/{s3_key}")

    print(f"\n✅ Uploaded {len(test_docs)} documents successfully")
    print("Documents are stored without KMS encryption for testing")

    return list(test_docs.keys())

if __name__ == "__main__":
    files = upload_simple_test_docs()
    print(f"\nNext step: Start ingestion job to process these {len(files)} files")
    print("Command: aws bedrock-agent start-ingestion-job --knowledge-base-id HFCMSKWHFU --data-source-id CZJWLDWEFD --region us-east-1")