# Creating Bedrock Knowledge Base - Console Guide

## Prerequisites Completed ✅
- S3 bucket: `jim-ai-forensic-data-1758988022`
- KMS key: `1ab7ed1d-4342-489a-ba66-1e448cf817d4`
- Data path: `s3://jim-ai-forensic-data-1758988022/kb/`

## Option A: Add Missing Permission
Add this permission to your IAM user, then run `./create-opensearch.sh`:
```json
{
  "Action": ["aoss:CreateCollection", "aoss:UpdateCollection", "aoss:DeleteCollection"],
  "Resource": "*",
  "Effect": "Allow"
}
```

## Option B: Console Setup (No Additional Permissions Needed)

### Step 1: Create Knowledge Base in Bedrock Console

1. **Navigate to Amazon Bedrock Console**
   - Go to: https://console.aws.amazon.com/bedrock/
   - Region: **us-east-1**

2. **Click "Knowledge bases" → "Create knowledge base"**

3. **Knowledge Base Details:**
   - Name: `jim-ai-forensic-kb`
   - Description: `Forensic document analysis knowledge base for JIM AI`
   - IAM permissions: Select **Create and use a new service role**

4. **Data Source Configuration:**
   - Click **Add data source**
   - Data source name: `jim-ai-s3-source`
   - S3 URI: `s3://jim-ai-forensic-data-1758988022/kb/`
   - Chunking strategy: **Default chunking**
   - Keep default parsing strategy

5. **Select Embeddings Model:**
   - Model: **Titan Text Embeddings V2**
   - Dimensions: **512** (good balance of performance/accuracy)

6. **Vector Database:**
   - Select: **Quick create a new vector store**
   - This will automatically create OpenSearch Serverless collection

7. **Review and Create**
   - Review all settings
   - Click **Create knowledge base**

### Step 2: Wait for Creation (5-10 minutes)

The console will:
1. Create OpenSearch Serverless collection
2. Set up proper IAM roles
3. Configure the vector index
4. Connect everything together

### Step 3: Test Knowledge Base

Once status shows **Ready**:
1. Click on your knowledge base name
2. Go to **Data sources** tab
3. Click **Sync** to start ingesting documents from S3

### Step 4: Save Configuration

After creation, note these values:
- Knowledge Base ID: `<will be shown in console>`
- OpenSearch Collection Endpoint: `<will be shown in console>`

Update `aws-resources.env` with the Knowledge Base ID.

## Testing the Knowledge Base

### Upload Test Document
```bash
echo "This is a test forensic document for JIM AI analysis." > test-doc.txt
python preprocess-files.py test-doc.txt
```

### Sync Knowledge Base
In console: Knowledge Base → Data sources → Select source → **Sync now**

### Test Query (After Sync Completes)
You can test in the console:
1. Go to your Knowledge Base
2. Click **Test knowledge base**
3. Enter: "What forensic documents do you have?"

## Next Steps

After Knowledge Base is created and synced:
1. Build the Lambda function for chat API
2. Create API Gateway
3. Connect frontend application

## Troubleshooting

If sync fails:
- Check S3 bucket permissions
- Ensure files in `/kb/` folder are supported formats
- Files must be ≤50MB (use preprocess-files.py)

If queries return no results:
- Wait for sync to complete (check status)
- Verify documents are in supported formats
- Check CloudWatch logs for errors