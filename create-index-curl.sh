#!/bin/bash

# Create OpenSearch index using AWS CLI and curl
COLLECTION_ENDPOINT="https://wpgjvevh88sli519jql9.us-east-1.aoss.amazonaws.com"
INDEX_NAME="bedrock-knowledge-base-default-index"
REGION="us-east-1"

# Create index mapping JSON
cat > /tmp/index_mapping.json << 'EOF'
{
  "settings": {
    "index": {
      "knn": true,
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
        "enabled": true
      }
    }
  }
}
EOF

echo "Creating OpenSearch index for Bedrock Knowledge Base..."
echo "Collection: $COLLECTION_ENDPOINT"
echo "Index: $INDEX_NAME"

# First check if index exists
echo "Checking if index exists..."
CHECK_RESPONSE=$(aws opensearchserverless batch-get-collection --names jim-ai-forensic-kb --region $REGION 2>/dev/null)

if [ $? -eq 0 ]; then
    echo "✅ Collection is accessible"

    # Create signed request using awscurl (if available) or fallback to console instructions
    if command -v awscurl &> /dev/null; then
        echo "Creating index using awscurl..."
        awscurl --service aoss --region $REGION \
            -X PUT \
            -H "Content-Type: application/json" \
            -d @/tmp/index_mapping.json \
            "$COLLECTION_ENDPOINT/$INDEX_NAME"
    else
        echo ""
        echo "=================================================="
        echo "Manual Index Creation Required"
        echo "=================================================="
        echo ""
        echo "Since awscurl is not available, please create the index manually:"
        echo ""
        echo "Option 1: Use OpenSearch Dashboards"
        echo "1. Go to: https://wpgjvevh88sli519jql9.us-east-1.aoss.amazonaws.com/_dashboards"
        echo "2. Navigate to Dev Tools"
        echo "3. Run this command:"
        echo ""
        echo "PUT /$INDEX_NAME"
        cat /tmp/index_mapping.json
        echo ""
        echo ""
        echo "Option 2: Alternative - Let Bedrock create the index"
        echo "In the Knowledge Base console, try using a different index name:"
        echo "Index Name: jim-ai-forensic-index"
        echo ""
        echo "The console may auto-create the index with proper mappings."
    fi
else
    echo "❌ Cannot access OpenSearch collection"
    echo "Please check your permissions and collection status"
fi

# Clean up
rm -f /tmp/index_mapping.json