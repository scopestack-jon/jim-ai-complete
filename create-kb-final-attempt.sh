#!/bin/bash

# Final attempt: Create Knowledge Base using existing OpenSearch collection

echo "Creating Knowledge Base with existing OpenSearch collection..."

# Configuration
KB_NAME="jim-ai-kb-final"
BUCKET_NAME="jim-ai-forensic-data-1758988022"
COLLECTION_ARN="arn:aws:aoss:us-east-1:447053376377:collection/uu1uqxhhebqq6f76llnk"
REGION="us-east-1"
ACCOUNT_ID="447053376377"

# Check if we have an existing role or need to create one
echo "Checking for existing IAM role..."
ROLE_EXISTS=$(aws iam get-role --role-name AmazonBedrockExecutionRoleForKnowledgeBase_jim-ai 2>/dev/null || echo "not-found")

if echo "$ROLE_EXISTS" | grep -q "not-found"; then
    echo "Creating new IAM role for Knowledge Base..."

    # Create trust policy
    cat > /tmp/kb-trust-policy-final.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "bedrock.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

    # Create role
    aws iam create-role \
        --role-name AmazonBedrockExecutionRoleForKnowledgeBase_jim-ai \
        --assume-role-policy-document file:///tmp/kb-trust-policy-final.json \
        --description "Bedrock Knowledge Base execution role for JIM AI"

    # Create and attach policy
    cat > /tmp/kb-policy-final.json << EOF
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
      "Resource": "$COLLECTION_ARN"
    }
  ]
}
EOF

    aws iam put-role-policy \
        --role-name AmazonBedrockExecutionRoleForKnowledgeBase_jim-ai \
        --policy-name BedrockKnowledgeBasePolicy \
        --policy-document file:///tmp/kb-policy-final.json

    echo "Waiting for role to propagate..."
    sleep 15

    ROLE_ARN="arn:aws:iam::$ACCOUNT_ID:role/AmazonBedrockExecutionRoleForKnowledgeBase_jim-ai"
else
    echo "Using existing role..."
    ROLE_ARN=$(echo "$ROLE_EXISTS" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['Role']['Arn'])" 2>/dev/null)
fi

echo "Role ARN: $ROLE_ARN"

# Create Knowledge Base with minimal configuration
echo "Creating Knowledge Base..."

KB_RESPONSE=$(aws bedrock-agent create-knowledge-base \
    --name "$KB_NAME" \
    --description "JIM AI Forensic Knowledge Base - Final Attempt" \
    --role-arn "$ROLE_ARN" \
    --knowledge-base-configuration '{
        "type": "VECTOR",
        "vectorKnowledgeBaseConfiguration": {
            "embeddingModelArn": "arn:aws:bedrock:'$REGION'::foundation-model/amazon.titan-embed-text-v2:0",
            "embeddingModelConfiguration": {
                "bedrockEmbeddingModelConfiguration": {
                    "dimensions": 1024
                }
            }
        }
    }' \
    --storage-configuration '{
        "type": "OPENSEARCH_SERVERLESS",
        "opensearchServerlessConfiguration": {
            "collectionArn": "'$COLLECTION_ARN'",
            "vectorIndexName": "bedrock-kb-index",
            "fieldMapping": {
                "vectorField": "bedrock-knowledge-base-default-vector",
                "textField": "AMAZON_BEDROCK_TEXT_CHUNK",
                "metadataField": "AMAZON_BEDROCK_METADATA"
            }
        }
    }' \
    --region $REGION 2>&1)

echo "Response: $KB_RESPONSE"

# Check if successful
if echo "$KB_RESPONSE" | grep -q "knowledgeBaseId"; then
    KB_ID=$(echo "$KB_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('knowledgeBase', {}).get('knowledgeBaseId', ''))" 2>/dev/null)

    echo ""
    echo "✅ SUCCESS! Knowledge Base Created!"
    echo "Knowledge Base ID: $KB_ID"

    # Create data source
    echo "Creating data source..."
    DS_RESPONSE=$(aws bedrock-agent create-data-source \
        --knowledge-base-id "$KB_ID" \
        --name "jim-ai-s3-documents" \
        --description "S3 data source for JIM AI forensic documents" \
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

        # Update config file
        echo "" >> aws-resources.env
        echo "# Final Knowledge Base Configuration" >> aws-resources.env
        echo "KB_ID_FINAL=$KB_ID" >> aws-resources.env
        echo "DS_ID_FINAL=$DS_ID" >> aws-resources.env
        echo "KB_NAME_FINAL=$KB_NAME" >> aws-resources.env
        echo "COLLECTION_ARN_FINAL=$COLLECTION_ARN" >> aws-resources.env

        echo ""
        echo "🎉 COMPLETE! Ready for document ingestion!"
        echo "Next: python3 test-kb-ingestion.py"
    else
        echo "❌ Data source creation failed: $DS_RESPONSE"
    fi
else
    echo "❌ Knowledge Base creation failed: $KB_RESPONSE"
fi

# Clean up temp files
rm -f /tmp/kb-trust-policy-final.json /tmp/kb-policy-final.json