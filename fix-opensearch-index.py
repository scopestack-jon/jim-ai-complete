#!/usr/bin/env python3
"""
Fix OpenSearch Index for JIM AI Knowledge Base
Creates the required index mapping for Bedrock Knowledge Base
"""

import boto3
import requests
from requests_aws4auth import AWS4Auth
import json

def create_opensearch_index():
    """Create the bedrock-kb-index with proper mapping"""

    # AWS credentials and region
    region = 'us-east-1'
    service = 'aoss'

    # Get AWS credentials
    session = boto3.Session()
    credentials = session.get_credentials()

    # Create AWS4Auth for OpenSearch Serverless
    awsauth = AWS4Auth(
        credentials.access_key,
        credentials.secret_key,
        region,
        service,
        session_token=credentials.token
    )

    # OpenSearch Serverless endpoint
    host = 'https://uu1uqxhhebqq6f76llnk.us-east-1.aoss.amazonaws.com'
    index_name = 'bedrock-kb-index'

    # Index mapping - simplified for OpenSearch Serverless
    index_mapping = {
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

    try:
        print(f"🔧 Creating OpenSearch index: {index_name}")
        print(f"📍 Endpoint: {host}")

        # Check if index exists first
        check_url = f"{host}/{index_name}"
        check_response = requests.get(check_url, auth=awsauth)

        if check_response.status_code == 200:
            print("⚠️  Index already exists. Deleting first...")
            delete_response = requests.delete(check_url, auth=awsauth)
            if delete_response.status_code in [200, 404]:
                print("✅ Old index deleted")
            else:
                print(f"❌ Failed to delete index: {delete_response.status_code}")
                print(delete_response.text)

        # Create the index
        create_url = f"{host}/{index_name}"
        response = requests.put(
            create_url,
            auth=awsauth,
            headers={'Content-Type': 'application/json'},
            json=index_mapping
        )

        if response.status_code in [200, 201]:
            print("✅ Index created successfully!")
            result = response.json()
            print(f"📄 Response: {json.dumps(result, indent=2)}")

            # Verify the index
            print("\n🔍 Verifying index creation...")
            verify_response = requests.get(create_url, auth=awsauth)
            if verify_response.status_code == 200:
                print("✅ Index verification successful!")
                verify_result = verify_response.json()
                mappings = verify_result.get(index_name, {}).get('mappings', {})
                properties = mappings.get('properties', {})

                if 'bedrock-knowledge-base-default-vector' in properties:
                    vector_config = properties['bedrock-knowledge-base-default-vector']
                    print(f"📊 Vector field configured: {vector_config.get('dimension')} dimensions")

                if 'AMAZON_BEDROCK_TEXT_CHUNK' in properties:
                    print("📝 Text chunk field configured")

                return True
            else:
                print(f"❌ Index verification failed: {verify_response.status_code}")
                return False

        else:
            print(f"❌ Failed to create index: {response.status_code}")
            print(f"📄 Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Error creating index: {str(e)}")
        return False

def test_knowledge_base():
    """Test the Knowledge Base after index creation"""
    try:
        print("\n🧪 Testing Knowledge Base connection...")

        bedrock_client = boto3.client('bedrock-agent-runtime', region_name='us-east-1')

        response = bedrock_client.retrieve_and_generate(
            input={'text': 'Hello, can you tell me about the documents available?'},
            retrieveAndGenerateConfiguration={
                'type': 'KNOWLEDGE_BASE',
                'knowledgeBaseConfiguration': {
                    'knowledgeBaseId': 'HFCMSKWHFU',
                    'modelArn': 'arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-5-sonnet-20240620-v1:0'
                }
            }
        )

        print("✅ Knowledge Base test successful!")
        answer = response.get('output', {}).get('text', 'No response')
        print(f"📝 Response: {answer[:200]}...")
        return True

    except Exception as e:
        print(f"❌ Knowledge Base test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 JIM AI OpenSearch Index Fix")
    print("=" * 50)

    # Step 1: Create the index
    if create_opensearch_index():
        print("\n" + "=" * 50)

        # Step 2: Test the Knowledge Base
        if test_knowledge_base():
            print("\n🎉 SUCCESS! Your Knowledge Base is now ready!")
            print("✅ You can now:")
            print("   - Upload files through the web interface")
            print("   - Process large data with large-data-processor.py")
            print("   - Query your documents through http://localhost:8080")
        else:
            print("\n⚠️  Index created but Knowledge Base test failed.")
            print("   This might be normal if no documents are uploaded yet.")
            print("   Try uploading some files first.")
    else:
        print("\n❌ Failed to create index. Check your AWS permissions.")
        print("   Make sure your IAM user has OpenSearch Serverless access.")