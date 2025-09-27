# JIM AI AWS Manual Setup Guide

Since your IAM user (`jim-ai-s3-user`) has limited permissions, you'll need to either:
1. Get the permissions upgraded by your AWS administrator
2. Perform these steps using an admin account

## Required Permissions

Share the `required-iam-policy.json` file with your AWS administrator to grant necessary permissions to your IAM user.

## Manual Setup Steps in AWS Console

### 1. Enable Bedrock Access (us-east-1)
1. Navigate to **Amazon Bedrock** service
2. Click **Model access** in left navigation
3. Click **Manage model access**
4. Enable these models:
   - Anthropic Claude 3.5 Sonnet
   - Amazon Titan Text Embeddings V2
5. Submit request (usually instant approval)

### 2. Create KMS Key
1. Navigate to **KMS** service
2. Click **Create key**
3. Choose **Symmetric** key type
4. Set alias: `jim-ai-forensic-key`
5. Add your IAM user as key administrator and user

### 3. Create S3 Bucket
1. Navigate to **S3** service
2. Click **Create bucket**
3. Bucket name: `jim-ai-forensic-data-[unique-suffix]`
4. Region: `us-east-1`
5. Configure settings:
   - **Versioning**: Enable
   - **Encryption**: AWS-KMS, use the key created above
   - **Public access**: Block all public access
   - **Transfer acceleration**: Enable
6. Create folder structure:
   - `raw/` - for original forensic files
   - `kb/` - for processed files (≤50MB each)
   - `processed/` - for intermediate processing

### 4. Create OpenSearch Serverless Collection
1. Navigate to **OpenSearch Service**
2. Choose **Serverless**
3. Click **Create collection**
4. Name: `jim-ai-forensic-collection`
5. Type: **Vector search**
6. Configure network: Public or VPC (recommend VPC for production)
7. Create data access policy for Bedrock

### 5. Create Bedrock Knowledge Base
1. Navigate to **Amazon Bedrock**
2. Click **Knowledge bases** → **Create**
3. Configuration:
   - Name: `jim-ai-forensic-kb`
   - IAM role: Create new (automatic)
   - Data source: S3
   - S3 URI: `s3://[your-bucket]/kb/`
   - Vector database: OpenSearch Serverless
   - Collection: Select the one created above
   - Embedding model: Titan Text Embeddings V2
   - Vector dimensions: 512

### 6. Create Lambda Function for API
1. Navigate to **Lambda**
2. Create function:
   - Name: `jim-ai-chat-api`
   - Runtime: Python 3.11
   - Create new execution role with Bedrock permissions
3. Add environment variables:
   - `KB_ID`: Your Knowledge Base ID
   - `MODEL_ARN`: `arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-5-sonnet-20240620-v1:0`

### 7. Create API Gateway
1. Navigate to **API Gateway**
2. Create REST API
3. Create resource `/chat`
4. Create POST method linked to Lambda function
5. Enable CORS if needed
6. Deploy to stage

## Post-Setup Configuration

Once resources are created, update your local configuration files with the actual values:
- Bucket name
- KMS key ID
- Knowledge Base ID
- API Gateway endpoint
- OpenSearch collection endpoint

## Granting Access to IAM User

After creating resources with an admin account, grant access to `jim-ai-s3-user`:

1. **S3 Bucket Policy**: Add policy allowing the IAM user full access
2. **KMS Key Policy**: Add the IAM user as key user
3. **Lambda Execution Role**: Grant invoke permissions
4. **Bedrock Knowledge Base**: Add IAM user to access policy