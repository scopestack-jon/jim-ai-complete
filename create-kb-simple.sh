#!/bin/bash

# Create Bedrock Knowledge Base - Simplified version

echo "Creating Bedrock Knowledge Base..."

# Configuration
KB_NAME="jim-ai-forensic-kb"
BUCKET_NAME="jim-ai-forensic-data-1758988022"
COLLECTION_ID="wpgjvevh88sli519jql9"
REGION="us-east-1"
ACCOUNT_ID="447053376377"
ROLE_ARN="arn:aws:iam::447053376377:role/JIM-AI-KnowledgeBase-Role"

echo "Using existing IAM role: $ROLE_ARN"

# Create the Knowledge Base
echo "Creating Knowledge Base..."

KB_RESPONSE=$(aws bedrock-agent create-knowledge-base \
    --name "$KB_NAME" \
    --description "Forensic document analysis knowledge base for JIM AI" \
    --role-arn "$ROLE_ARN" \
    --knowledge-base-configuration '{
        "type": "VECTOR",
        "vectorKnowledgeBaseConfiguration": {
            "embeddingModelArn": "arn:aws:bedrock:'$REGION'::foundation-model/amazon.titan-embed-text-v2:0",
            "embeddingModelConfiguration": {
                "bedrockEmbeddingModelConfiguration": {
                    "dimensions": 512
                }
            }
        }
    }' \
    --storage-configuration '{
        "type": "OPENSEARCH_SERVERLESS",
        "opensearchServerlessConfiguration": {
            "collectionArn": "arn:aws:aoss:'$REGION':'$ACCOUNT_ID':collection/'$COLLECTION_ID'",
            "vectorIndexName": "bedrock-knowledge-base-default-index",
            "fieldMapping": {
                "vectorField": "bedrock-knowledge-base-default-vector",
                "textField": "AMAZON_BEDROCK_TEXT_CHUNK",
                "metadataField": "AMAZON_BEDROCK_METADATA"
            }
        }
    }' \
    --region $REGION 2>&1)

# Check if successful
if echo "$KB_RESPONSE" | grep -q "knowledgeBaseId"; then
    # Extract Knowledge Base ID
    KB_ID=$(echo "$KB_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('knowledgeBase', {}).get('knowledgeBaseId', ''))" 2>/dev/null)

    echo ""
    echo "=================================="
    echo "✅ Knowledge Base Created!"
    echo "=================================="
    echo "Knowledge Base ID: $KB_ID"
    echo "Name: $KB_NAME"
    echo ""

    # Create data source
    echo "Creating S3 data source..."

    DS_RESPONSE=$(aws bedrock-agent create-data-source \
        --knowledge-base-id "$KB_ID" \
        --name "jim-ai-s3-source" \
        --description "S3 data source for forensic documents" \
        --data-source-configuration '{
            "type": "S3",
            "s3Configuration": {
                "bucketArn": "arn:aws:s3:::'$BUCKET_NAME'",
                "inclusionPrefixes": ["kb/"]
            }
        }' \
        --region $REGION 2>&1)

    if echo "$DS_RESPONSE" | grep -q "dataSourceId"; then
        DS_ID=$(echo "$DS_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('dataSource', {}).get('dataSourceId', ''))" 2>/dev/null)

        echo "✅ Data Source Created!"
        echo "Data Source ID: $DS_ID"
        echo ""
        echo "Configuration saved to aws-resources.env"

        # Update configuration file
        echo "KB_ID=$KB_ID" >> aws-resources.env
        echo "DS_ID=$DS_ID" >> aws-resources.env

        echo ""
        echo "Next steps:"
        echo "1. Upload documents: python3 test-kb-ingestion.py"
        echo "2. Start ingestion: aws bedrock-agent start-ingestion-job --knowledge-base-id $KB_ID --data-source-id $DS_ID"

    else
        echo "❌ Data Source creation failed:"
        echo "$DS_RESPONSE"
    fi

else
    echo "❌ Knowledge Base creation failed:"
    echo "$KB_RESPONSE"
fi