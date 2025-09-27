#!/bin/bash

# Create OpenSearch Serverless Collection for JIM AI

echo "Creating OpenSearch Serverless collection..."

COLLECTION_NAME="jim-ai-forensic-kb"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION="us-east-1"

# Step 1: Create encryption policy
echo "Creating encryption policy..."
aws opensearchserverless create-security-policy \
  --name "${COLLECTION_NAME}-encryption" \
  --type encryption \
  --policy "{
    \"Rules\": [{
      \"ResourceType\": \"collection\",
      \"Resource\": [\"collection/${COLLECTION_NAME}\"]
    }],
    \"AWSOwnedKey\": true
  }" \
  --region $REGION

# Step 2: Create network policy (public access)
echo "Creating network policy..."
aws opensearchserverless create-security-policy \
  --name "${COLLECTION_NAME}-network" \
  --type network \
  --policy "[{
    \"Description\": \"Public access for ${COLLECTION_NAME}\",
    \"Rules\": [{
      \"ResourceType\": \"collection\",
      \"Resource\": [\"collection/${COLLECTION_NAME}\"]
    }, {
      \"ResourceType\": \"dashboard\",
      \"Resource\": [\"collection/${COLLECTION_NAME}\"]
    }],
    \"AllowFromPublic\": true
  }]" \
  --region $REGION

# Step 3: Create data access policy
echo "Creating data access policy..."
aws opensearchserverless create-access-policy \
  --name "${COLLECTION_NAME}-access" \
  --type data \
  --policy "[{
    \"Rules\": [{
      \"ResourceType\": \"collection\",
      \"Resource\": [\"collection/${COLLECTION_NAME}\"],
      \"Permission\": [
        \"aoss:CreateCollectionItems\",
        \"aoss:UpdateCollectionItems\",
        \"aoss:DescribeCollectionItems\",
        \"aoss:DeleteCollectionItems\"
      ]
    }, {
      \"ResourceType\": \"index\",
      \"Resource\": [\"index/${COLLECTION_NAME}/*\"],
      \"Permission\": [
        \"aoss:CreateIndex\",
        \"aoss:UpdateIndex\",
        \"aoss:DescribeIndex\",
        \"aoss:DeleteIndex\",
        \"aoss:ReadDocument\",
        \"aoss:WriteDocument\"
      ]
    }],
    \"Principal\": [
      \"arn:aws:iam::${ACCOUNT_ID}:user/jim-ai-s3-user\",
      \"arn:aws:iam::${ACCOUNT_ID}:root\"
    ]
  }]" \
  --region $REGION

# Step 4: Create the collection
echo "Creating OpenSearch Serverless collection..."
COLLECTION_RESPONSE=$(aws opensearchserverless create-collection \
  --name "${COLLECTION_NAME}" \
  --type VECTORSEARCH \
  --description "Vector search collection for JIM AI forensic knowledge base" \
  --region $REGION)

# Extract collection details (macOS compatible)
COLLECTION_ID=$(echo $COLLECTION_RESPONSE | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('createCollectionDetail', {}).get('id', ''))")
COLLECTION_ARN=$(echo $COLLECTION_RESPONSE | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('createCollectionDetail', {}).get('arn', ''))")

echo ""
echo "=================================="
echo "OpenSearch Collection Created!"
echo "=================================="
echo "Collection Name: ${COLLECTION_NAME}"
echo "Collection ID: ${COLLECTION_ID}"
echo "Collection ARN: ${COLLECTION_ARN}"
echo ""
echo "The collection is being created. Status can be checked with:"
echo "aws opensearchserverless batch-get-collection --names ${COLLECTION_NAME}"
echo ""
echo "Wait for status to be ACTIVE before creating Knowledge Base (usually 1-2 minutes)"