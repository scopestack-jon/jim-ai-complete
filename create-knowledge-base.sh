#!/bin/bash

# Create Bedrock Knowledge Base

echo "Creating Bedrock Knowledge Base..."

# Configuration
KB_NAME="jim-ai-forensic-kb"
BUCKET_NAME="jim-ai-forensic-data-1758988022"
COLLECTION_ID="wpgjvevh88sli519jql9"
REGION="us-east-1"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# First, check if OpenSearch collection is ACTIVE
echo "Checking OpenSearch collection status..."
COLLECTION_STATUS=$(aws opensearchserverless batch-get-collection --names jim-ai-forensic-kb --region $REGION --query 'collectionDetails[0].status' --output text)

if [ "$COLLECTION_STATUS" != "ACTIVE" ]; then
    echo "❌ OpenSearch collection is not ACTIVE yet (status: $COLLECTION_STATUS)"
    echo "Please wait for collection to be ACTIVE before creating Knowledge Base"
    echo "Check status with: aws opensearchserverless batch-get-collection --names jim-ai-forensic-kb"
    exit 1
fi

echo "✅ OpenSearch collection is ACTIVE"

# Get collection endpoint
COLLECTION_ENDPOINT=$(aws opensearchserverless batch-get-collection --names jim-ai-forensic-kb --region $REGION --query 'collectionDetails[0].collectionEndpoint' --output text)
echo "Collection endpoint: $COLLECTION_ENDPOINT"

# Create IAM role for Knowledge Base
echo "Creating IAM role for Knowledge Base..."

# Trust policy for Bedrock
cat > /tmp/kb-trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "bedrock.amazonaws.com"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "aws:SourceAccount": "$ACCOUNT_ID"
        },
        "ArnLike": {
          "aws:SourceArn": "arn:aws:bedrock:$REGION:$ACCOUNT_ID:knowledge-base/*"
        }
      }
    }
  ]
}
EOF

# Create the role
aws iam create-role \
    --role-name JIM-AI-KnowledgeBase-Role \
    --assume-role-policy-document file:///tmp/kb-trust-policy.json \
    --description "IAM role for JIM AI Bedrock Knowledge Base"

# Create and attach policy for S3 access
cat > /tmp/kb-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::$BUCKET_NAME",
        "arn:aws:s3:::$BUCKET_NAME/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": "arn:aws:bedrock:$REGION::foundation-model/amazon.titan-embed-text-v2:0"
    },
    {
      "Effect": "Allow",
      "Action": [
        "aoss:APIAccessAll"
      ],
      "Resource": "arn:aws:aoss:$REGION:$ACCOUNT_ID:collection/$COLLECTION_ID"
    }
  ]
}
EOF

aws iam put-role-policy \
    --role-name JIM-AI-KnowledgeBase-Role \
    --policy-name JIM-AI-KnowledgeBase-Policy \
    --policy-document file:///tmp/kb-policy.json

# Wait for role to propagate
echo "Waiting for IAM role to propagate..."
sleep 10

# Create the Knowledge Base
echo "Creating Knowledge Base..."

KB_RESPONSE=$(aws bedrock-agent create-knowledge-base \
    --name "$KB_NAME" \
    --description "Forensic document analysis knowledge base for JIM AI" \
    --role-arn "arn:aws:iam::$ACCOUNT_ID:role/JIM-AI-KnowledgeBase-Role" \
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
            "vectorIndexName": "jim-ai-forensic-index",
            "fieldMapping": {
                "vectorField": "embedding",
                "textField": "text",
                "metadataField": "metadata"
            }
        }
    }' \
    --region $REGION)

# Extract Knowledge Base ID
KB_ID=$(echo $KB_RESPONSE | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('knowledgeBase', {}).get('knowledgeBaseId', ''))")

echo ""
echo "=================================="
echo "Knowledge Base Created!"
echo "=================================="
echo "Knowledge Base ID: $KB_ID"
echo "Name: $KB_NAME"
echo "Status: Creating (will take a few moments)"

# Create data source
echo ""
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
    --region $REGION)

DS_ID=$(echo $DS_RESPONSE | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('dataSource', {}).get('dataSourceId', ''))")

echo "Data Source ID: $DS_ID"
echo ""
echo "Setup complete! Save these values:"
echo "KB_ID=$KB_ID"
echo "DS_ID=$DS_ID"
echo ""
echo "Next steps:"
echo "1. Upload documents to s3://$BUCKET_NAME/kb/"
echo "2. Sync the data source: aws bedrock-agent start-ingestion-job --knowledge-base-id $KB_ID --data-source-id $DS_ID"

# Clean up temp files
rm -f /tmp/kb-trust-policy.json /tmp/kb-policy.json