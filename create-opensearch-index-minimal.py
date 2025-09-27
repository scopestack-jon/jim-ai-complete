#!/usr/bin/env python3 --break-system-packages

import json
import subprocess

def create_index_with_curl():
    """Create OpenSearch index using curl with AWS signature"""

    # Index mapping
    mapping = {
        "settings": {
            "index.knn": True
        },
        "mappings": {
            "properties": {
                "bedrock-knowledge-base-default-vector": {
                    "type": "knn_vector",
                    "dimension": 512,
                    "method": {
                        "name": "hnsw",
                        "space_type": "cosinesimil",
                        "engine": "faiss"
                    }
                },
                "AMAZON_BEDROCK_TEXT_CHUNK": {
                    "type": "text"
                },
                "AMAZON_BEDROCK_METADATA": {
                    "type": "object"
                }
            }
        }
    }

    # Write mapping to file
    with open('/tmp/index_mapping.json', 'w') as f:
        json.dump(mapping, f, indent=2)

    print("Creating OpenSearch index...")
    print("Index: jim-forensic-index")

    # Use AWS CLI with opensearch-py approach
    endpoint = "https://wpgjvevh88sli519jql9.us-east-1.aoss.amazonaws.com"
    index_name = "jim-forensic-index"

    # Try using Python opensearch-py with AWS auth
    try:
        import boto3
        from opensearchpy import OpenSearch, RequestsHttpConnection
        from requests_aws4auth import AWS4Auth

        # Get AWS credentials
        session = boto3.Session()
        credentials = session.get_credentials()
        awsauth = AWS4Auth(
            credentials.access_key,
            credentials.secret_key,
            'us-east-1',
            'aoss',
            session_token=credentials.token
        )

        # Create OpenSearch client
        client = OpenSearch(
            hosts=[{'host': 'wpgjvevh88sli519jql9.us-east-1.aoss.amazonaws.com', 'port': 443}],
            http_auth=awsauth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
            timeout=60
        )

        # Create index
        response = client.indices.create(
            index=index_name,
            body=mapping
        )

        print(f"✅ Index created successfully!")
        print(f"Response: {response}")
        return True

    except ImportError:
        print("❌ Required packages not available")
        print("Run: pip install opensearch-py requests-aws4auth")
        return False
    except Exception as e:
        print(f"❌ Error creating index: {e}")
        return False

if __name__ == "__main__":
    create_index_with_curl()