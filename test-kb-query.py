#!/usr/bin/env python3
"""
Test Knowledge Base queries
"""

import boto3
import json

def test_knowledge_base_query():
    """Test querying the Knowledge Base"""

    # Configuration
    KB_ID = "HFCMSKWHFU"
    MODEL_ARN = "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-5-sonnet-20240620-v1:0"
    REGION = "us-east-1"

    # Create Bedrock client
    bedrock_client = boto3.client('bedrock-agent-runtime', region_name=REGION)

    # Test queries for forensic data
    test_queries = [
        "What case is this about?",
        "What evidence was collected?",
        "What were the key findings in the investigation?",
        "Tell me about the network forensics analysis",
        "What malware was found?",
        "What was the timeline of events?"
    ]

    print("Testing Knowledge Base queries...")
    print(f"Knowledge Base ID: {KB_ID}")
    print("=" * 50)

    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Query: {query}")
        print("-" * 30)

        try:
            response = bedrock_client.retrieve_and_generate(
                input={'text': query},
                retrieveAndGenerateConfiguration={
                    'type': 'KNOWLEDGE_BASE',
                    'knowledgeBaseConfiguration': {
                        'knowledgeBaseId': KB_ID,
                        'modelArn': MODEL_ARN
                    }
                }
            )

            # Extract answer and sources
            answer = response['output']['text']
            sources = response.get('citations', [])

            print(f"Answer: {answer}")

            if sources:
                print("\nSources:")
                for j, citation in enumerate(sources, 1):
                    for ref in citation.get('retrievedReferences', []):
                        location = ref.get('location', {}).get('s3Location', {})
                        uri = location.get('uri', 'Unknown')
                        print(f"  {j}. {uri}")
            else:
                print("\nNo sources found")

        except Exception as e:
            print(f"Error: {str(e)}")

        print()

if __name__ == "__main__":
    test_knowledge_base_query()