#!/bin/bash

echo "Monitoring OpenSearch collection status..."
echo "Collection: jim-ai-forensic-kb"
echo "Started at: $(date)"
echo ""

while true; do
    STATUS=$(aws opensearchserverless batch-get-collection --names jim-ai-forensic-kb --region us-east-1 --query 'collectionDetails[0].status' --output text 2>/dev/null)

    if [ "$STATUS" = "ACTIVE" ]; then
        echo "✅ Collection is ACTIVE!"
        echo "You can now run: ./create-knowledge-base.sh"
        break
    elif [ "$STATUS" = "FAILED" ]; then
        echo "❌ Collection creation FAILED"
        break
    else
        echo "⏳ Status: $STATUS ($(date +%H:%M:%S))"
        sleep 30
    fi
done