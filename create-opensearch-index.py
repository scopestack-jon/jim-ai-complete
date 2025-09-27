#!/usr/bin/env python3
"""
Create OpenSearch index for Bedrock Knowledge Base
"""

import boto3
import requests
from requests.auth import HTTPBasicAuth
import json

def create_opensearch_index():
    """Create the required index in OpenSearch Serverless collection"""

    # Configuration
    COLLECTION_ENDPOINT = "https://wpgjvevh88sli519jql9.us-east-1.aoss.amazonaws.com"
    INDEX_NAME = "bedrock-knowledge-base-default-index"
    REGION = "us-east-1"

    # Create AWS session for signing requests
    session = boto3.Session()
    credentials = session.get_credentials()

    # Index mapping for Bedrock Knowledge Base
    index_mapping = {
        "settings": {
            "index": {
                "knn": True,
                "knn.algo_param.ef_search": 512,
                "knn.algo_param.ef_construction": 512
            }
        },
        "mappings": {
            "properties": {
                "bedrock-knowledge-base-default-vector": {
                    "type": "knn_vector",
                    "dimension": 512,
                    "method": {
                        "name": "hnsw",
                        "space_type": "cosinesimil",
                        "engine": "faiss",
                        "parameters": {
                            "ef_construction": 512,
                            "m": 16
                        }
                    }
                },
                "AMAZON_BEDROCK_TEXT_CHUNK": {
                    "type": "text"
                },
                "AMAZON_BEDROCK_METADATA": {
                    "type": "object",
                    "enabled": True
                }
            }
        }
    }

    # Sign the request using AWS credentials
    from botocore.auth import SigV4Auth
    from botocore.awsrequest import AWSRequest

    url = f"{COLLECTION_ENDPOINT}/{INDEX_NAME}"
    headers = {
        'Content-Type': 'application/json'
    }

    request = AWSRequest(
        method='PUT',
        url=url,
        data=json.dumps(index_mapping),
        headers=headers
    )

    SigV4Auth(credentials, 'aoss', REGION).add_auth(request)

    # Make the request
    response = requests.put(
        url,
        data=json.dumps(index_mapping),
        headers=dict(request.headers)
    )

    if response.status_code in [200, 201]:
        print(f"✅ Index '{INDEX_NAME}' created successfully!")
        print(f"Response: {response.json()}")
        return True
    else:
        print(f"❌ Failed to create index. Status: {response.status_code}")
        print(f"Response: {response.text}")
        return False

def check_index_exists():
    """Check if the index already exists"""

    COLLECTION_ENDPOINT = "https://wpgjvevh88sli519jql9.us-east-1.aoss.amazonaws.com"
    INDEX_NAME = "bedrock-knowledge-base-default-index"
    REGION = "us-east-1"

    session = boto3.Session()
    credentials = session.get_credentials()

    from botocore.auth import SigV4Auth
    from botocore.awsrequest import AWSRequest

    url = f"{COLLECTION_ENDPOINT}/{INDEX_NAME}"

    request = AWSRequest(method='GET', url=url)
    SigV4Auth(credentials, 'aoss', REGION).add_auth(request)

    response = requests.get(url, headers=dict(request.headers))

    if response.status_code == 200:
        print(f"✅ Index '{INDEX_NAME}' already exists")
        return True
    elif response.status_code == 404:
        print(f"❌ Index '{INDEX_NAME}' does not exist")
        return False
    else:
        print(f"⚠️  Unexpected response: {response.status_code}")
        print(f"Response: {response.text}")
        return False

if __name__ == "__main__":
    print("Checking OpenSearch index for Bedrock Knowledge Base...")

    # Check if index exists
    if check_index_exists():
        print("Index is ready for Knowledge Base creation!")
    else:
        print("Creating index...")
        if create_opensearch_index():
            print("\n✅ Index creation completed!")
            print("You can now retry creating the Knowledge Base in the console.")
        else:
            print("\n❌ Index creation failed.")
            print("Please check your OpenSearch permissions and collection status.")