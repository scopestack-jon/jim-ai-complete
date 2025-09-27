# Knowledge Base Creation Failure - Troubleshooting Guide

## Likely Causes of Failure

Based on the error pattern, the most common causes are:

### 1. **OpenSearch Access Policy Conflicts**
Multiple access policies exist:
- `jim-ai-forensic-kb-access` (from our CLI setup)
- `bedrock-knowledge-base-50s0ev` (from failed console attempt)

These may have conflicting permissions.

### 2. **IAM Role Issues**
The service role may not have proper permissions for the OpenSearch collection.

## **Recommended Fix: Clean Slate Approach**

### Step 1: Create Fresh Knowledge Base with New Collection

In the Bedrock console:

1. **Knowledge Base Details:**
   - Name: `jim-forensic-kb-final`
   - Description: `Forensic analysis knowledge base - clean setup`
   - IAM role: **Create and use a new service role**

2. **Data Source:**
   - S3 URI: `s3://jim-ai-forensic-data-1758988022/kb/`
   - Default chunking strategy

3. **Embedding Model:**
   - **Titan Text Embeddings V2**
   - Dimensions: **512**

4. **Vector Database:**
   - Select: **Quick create a new vector store**
   - Collection name: `forensic-kb-final`

**Why this works:**
- Fresh collection avoids policy conflicts
- New service role gets proper auto-generated permissions
- No interference from previous failed attempts

### Step 2: Alternative - Fix Existing Collection

If you want to use the existing collection, clean up first:

```bash
# Delete conflicting access policy
aws opensearchserverless delete-access-policy \
    --name bedrock-knowledge-base-50s0ev \
    --type data \
    --region us-east-1

# Then retry with existing collection
```

## **Recommended: Try Fresh Setup First**

The quickest path to success is creating a new Knowledge Base with auto-generated resources. This avoids all the permission conflicts and gets you operational faster.

## **After Successful Creation**

1. **Note the Knowledge Base ID**
2. **Test ingestion**: Upload a small test file to `/kb/` folder
3. **Sync**: Start ingestion job in console
4. **Test queries**: Use console's test feature

## **Next Steps After KB is Working**

1. Upload forensic documents using `preprocess-files.py`
2. Build the Lambda chat API
3. Create the frontend interface

The key is getting past this creation hurdle - once the Knowledge Base exists, everything else is straightforward.