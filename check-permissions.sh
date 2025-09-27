#!/bin/bash

# Check AWS permissions and current setup
echo "==================================="
echo "AWS Permission Check for JIM AI Setup"
echo "==================================="

# Get current user identity
echo "Current AWS Identity:"
aws sts get-caller-identity

echo ""
echo "==================================="
echo "Checking S3 Permissions..."
echo "==================================="

# List existing buckets
echo "Existing buckets you can access:"
aws s3 ls

echo ""
echo "==================================="
echo "Required IAM Permissions Missing:"
echo "==================================="
echo "Your IAM user (jim-ai-s3-user) needs the following permissions:"
echo ""
echo "1. KMS Permissions:"
echo "   - kms:CreateKey"
echo "   - kms:CreateAlias"
echo "   - kms:DescribeKey"
echo "   - kms:ListAliases"
echo ""
echo "2. S3 Permissions:"
echo "   - s3:CreateBucket"
echo "   - s3:PutBucketVersioning"
echo "   - s3:PutBucketEncryption"
echo "   - s3:PutPublicAccessBlock"
echo "   - s3:PutAccelerateConfiguration"
echo ""
echo "3. Bedrock Permissions (for later):"
echo "   - bedrock:*"
echo ""
echo "==================================="
echo "Next Steps:"
echo "==================================="
echo "Option 1: Ask your AWS administrator to add these permissions to your IAM user"
echo ""
echo "Option 2: Use an existing bucket that you have access to"
echo "          Update the BUCKET_NAME in aws-setup.sh to use an existing bucket"
echo ""
echo "Option 3: Create resources manually in AWS Console with an admin account"
echo "          Then grant your IAM user access to those resources"