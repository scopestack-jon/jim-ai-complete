#!/bin/bash

echo "Checking OpenSearch Serverless permissions..."

# Test if we can create collections
echo -n "Testing aoss:CreateCollection permission... "

# Try to do a dry-run describe (won't actually create anything)
if aws opensearchserverless list-collections --region us-east-1 2>/dev/null 1>/dev/null; then
    echo "✓ Can list collections"

    # Check if we have any existing collections from previous attempts
    COLLECTIONS=$(aws opensearchserverless list-collections --region us-east-1 --query 'collectionSummaries[*].name' --output text 2>/dev/null)

    if [ ! -z "$COLLECTIONS" ]; then
        echo "Found existing collections: $COLLECTIONS"
    else
        echo "No existing collections found"
    fi

    echo ""
    echo "Once permissions are added, run: ./create-opensearch.sh"
else
    echo "✗ Still need aoss:CreateCollection permission"
    echo "Please have your admin add the permissions from additional-permissions.json"
fi