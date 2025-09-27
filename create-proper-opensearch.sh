#!/bin/bash
# Create properly configured OpenSearch Serverless collection for Bedrock KB

echo "🚀 Creating new OpenSearch Serverless collection with KNN enabled..."

COLLECTION_NAME="jim-ai-kb-production"
REGION="us-east-1"

# Create collection with VECTORSEARCH type (KNN enabled)
echo "📊 Creating OpenSearch collection..."
aws opensearchserverless create-collection \
    --name "$COLLECTION_NAME" \
    --type VECTORSEARCH \
    --description "Production OpenSearch for JIM AI with KNN enabled" \
    --region $REGION \
    --output json > opensearch-collection.json

if [ $? -eq 0 ]; then
    COLLECTION_ID=$(cat opensearch-collection.json | python3 -c "import sys, json; print(json.load(sys.stdin)['createCollectionDetail']['id'])")
    COLLECTION_ARN=$(cat opensearch-collection.json | python3 -c "import sys, json; print(json.load(sys.stdin)['createCollectionDetail']['arn'])")
    COLLECTION_ENDPOINT=$(cat opensearch-collection.json | python3 -c "import sys, json; print(json.load(sys.stdin)['createCollectionDetail']['collectionEndpoint'])")

    echo "✅ Collection created!"
    echo "   ID: $COLLECTION_ID"
    echo "   ARN: $COLLECTION_ARN"
    echo "   Endpoint: $COLLECTION_ENDPOINT"

    # Create data access policy
    echo "🔒 Creating data access policy..."
    cat > data-access-policy.json <<EOF
{
    "name": "jim-ai-kb-data-access",
    "type": "data",
    "description": "Data access for JIM AI Knowledge Base",
    "policy": "[{\"Rules\":[{\"ResourceType\":\"collection\",\"Resource\":[\"collection/$COLLECTION_NAME\"],\"Permission\":[\"aoss:CreateCollectionItems\",\"aoss:UpdateCollectionItems\",\"aoss:DescribeCollectionItems\",\"aoss:DeleteCollectionItems\"]},{\"ResourceType\":\"index\",\"Resource\":[\"index/$COLLECTION_NAME/*\"],\"Permission\":[\"aoss:CreateIndex\",\"aoss:UpdateIndex\",\"aoss:DescribeIndex\",\"aoss:ReadDocument\",\"aoss:WriteDocument\",\"aoss:DeleteIndex\"]}],\"Principal\":[\"arn:aws:iam::447053376377:role/service-role/AmazonBedrockExecutionRoleForKnowledgeBase_jim-ai\",\"arn:aws:iam::447053376377:user/jim-ai-s3-user\"]}]"
}
EOF

    aws opensearchserverless create-access-policy \
        --cli-input-json file://data-access-policy.json \
        --region $REGION

    # Create network policy
    echo "🌐 Creating network policy..."
    cat > network-policy.json <<EOF
{
    "name": "jim-ai-kb-network",
    "type": "network",
    "description": "Network access for JIM AI Knowledge Base",
    "policy": "[{\"Rules\":[{\"ResourceType\":\"dashboard\",\"Resource\":[\"collection/$COLLECTION_NAME\"]},{\"ResourceType\":\"collection\",\"Resource\":[\"collection/$COLLECTION_NAME\"]}],\"AllowFromPublic\":true}]"
}
EOF

    aws opensearchserverless create-security-policy \
        --cli-input-json file://network-policy.json \
        --region $REGION

    # Create encryption policy
    echo "🔐 Creating encryption policy..."
    cat > encryption-policy.json <<EOF
{
    "name": "jim-ai-kb-encryption",
    "type": "encryption",
    "description": "Encryption for JIM AI Knowledge Base",
    "policy": "{\"Rules\":[{\"ResourceType\":\"collection\",\"Resource\":[\"collection/$COLLECTION_NAME\"]}],\"AWSOwnedKey\":true}"
}
EOF

    aws opensearchserverless create-security-policy \
        --cli-input-json file://encryption-policy.json \
        --region $REGION

    echo "⏳ Waiting for collection to become ACTIVE..."
    while true; do
        STATUS=$(aws opensearchserverless batch-get-collection \
            --ids $COLLECTION_ID \
            --region $REGION \
            --query 'collectionDetails[0].status' \
            --output text)

        if [ "$STATUS" = "ACTIVE" ]; then
            echo "✅ Collection is ACTIVE!"
            break
        else
            echo "   Status: $STATUS (waiting...)"
            sleep 10
        fi
    done

    echo ""
    echo "✅ OpenSearch collection created successfully!"
    echo ""
    echo "📋 Collection Details:"
    echo "   Name: $COLLECTION_NAME"
    echo "   ID: $COLLECTION_ID"
    echo "   Endpoint: $COLLECTION_ENDPOINT"
    echo "   ARN: $COLLECTION_ARN"
    echo ""
    echo "🎯 Next Steps:"
    echo "   1. Create a new Knowledge Base in Bedrock Console"
    echo "   2. Select 'Choose existing vector store'"
    echo "   3. Select OpenSearch Serverless"
    echo "   4. Use this collection ARN: $COLLECTION_ARN"
    echo "   5. Create index name: bedrock-kb-index"
    echo "   6. Vector field: bedrock-knowledge-base-default-vector"
    echo "   7. Text field: AMAZON_BEDROCK_TEXT_CHUNK"
    echo "   8. Metadata field: AMAZON_BEDROCK_METADATA"
    echo ""
    echo "📝 Save these values for configuration!"

else
    echo "❌ Failed to create collection"
    exit 1
fi