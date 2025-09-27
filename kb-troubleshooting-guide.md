# Knowledge Base Creation Troubleshooting

## Current Status
- ✅ OpenSearch Collection: ACTIVE (`jim-ai-forensic-kb`)
- ✅ S3 Bucket: `jim-ai-forensic-data-1758988022`
- ❌ Knowledge Base: Creation failed

## Root Cause Analysis
The failure is likely due to one of these issues:

### 1. IAM Role Permissions Issue
The service role created by the console may not have sufficient permissions.

### 2. OpenSearch Access Policy Conflict
Multiple access policies might be conflicting.

### 3. Index Configuration Issue
The index name or mapping configuration is incompatible.

## Solution: Fresh Start with Console Auto-Creation

### Step 1: Clean Up Previous Attempt
```bash
# Delete the auto-created policy if it exists
aws opensearchserverless delete-access-policy \
    --name bedrock-knowledge-base-50s0ev \
    --type data \
    --region us-east-1
```

### Step 2: Create Knowledge Base with Simplified Settings

**In AWS Console (Bedrock → Knowledge bases → Create):**

1. **Knowledge Base Details:**
   - Name: `jim-forensic-kb-v2`
   - Description: `Forensic analysis knowledge base`
   - IAM permissions: **Create and use a new service role**

2. **Data Source:**
   - Name: `forensic-documents`
   - S3 URI: `s3://jim-ai-forensic-data-1758988022/kb/`
   - Chunking: **Default chunking**

3. **Embeddings Model:**
   - Model: **Titan Text Embeddings V2**
   - Dimensions: **1024** (try larger dimensions for better accuracy)

4. **Vector Database:**
   - Choose: **Quick create a new vector store**
   - Collection name: `jim-forensic-kb-v2`

**Why this approach works:**
- New collection avoids permission conflicts
- Console handles all IAM setup automatically
- Different name prevents conflicts with previous attempt

### Step 3: Alternative - Use Existing Collection with Manual Role

If you prefer to use the existing collection:

1. **Create IAM Role Manually First:**
   ```bash
   ./create-kb-role.sh
   ```

2. **In Console, select:**
   - IAM role: **Use an existing service role**
   - Role ARN: `arn:aws:iam::447053376377:role/JIM-AI-KnowledgeBase-Role`
   - Vector store: **Connect to existing**
   - Collection ARN: `arn:aws:aoss:us-east-1:447053376377:collection/wpgjvevh88sli519jql9`
   - Index name: `forensic-docs-index`

## Recommended Approach

**Try Option 1 (Quick create new vector store) first** - it's the most reliable approach as it handles all the complex IAM and OpenSearch configuration automatically.

## Common Issues and Solutions

### Issue: "Invalid storage configuration"
- **Solution**: Use "Quick create new vector store" instead of existing

### Issue: "IAM role cannot be assumed"
- **Solution**: Let console create the role automatically

### Issue: "Collection access denied"
- **Solution**: Use new collection with auto-generated policies

### Issue: "Index mapping incompatible"
- **Solution**: Let Bedrock create the index with proper mappings

## Next Steps After Successful Creation

1. **Note the Knowledge Base ID**
2. **Test with sample documents**: Run `python3 test-kb-ingestion.py`
3. **Verify ingestion works**: Check console for sync status
4. **Test queries**: Use console's "Test knowledge base" feature

## Monitoring Commands

```bash
# Check KB status
aws bedrock-agent list-knowledge-bases --region us-east-1

# Check collections
aws opensearchserverless list-collections --region us-east-1

# Check data access policies
aws opensearchserverless list-access-policies --type data --region us-east-1
```