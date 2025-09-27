#!/bin/bash

# AWS Setup Script for JIM AI Forensic Application
# Run this script after configuring your AWS credentials

# Configuration Variables
export AWS_REGION="us-east-1"
export BUCKET_NAME="jim-ai-forensic-data-$(date +%s)"  # Unique bucket name
export KMS_KEY_ALIAS="alias/jim-ai-forensic-key"
export KB_PREFIX="kb/"
export RAW_PREFIX="raw/"

echo "Starting AWS setup for JIM AI Forensic Application..."
echo "Region: $AWS_REGION"
echo "Bucket: $BUCKET_NAME"

# Step 1: Create KMS key for encryption
echo "Creating KMS key..."
KMS_KEY_ID=$(aws kms create-key \
    --description "JIM AI Forensic Application Encryption Key" \
    --region $AWS_REGION \
    --query 'KeyMetadata.KeyId' \
    --output text)

aws kms create-alias \
    --alias-name $KMS_KEY_ALIAS \
    --target-key-id $KMS_KEY_ID \
    --region $AWS_REGION

echo "KMS Key created: $KMS_KEY_ID"

# Step 2: Create S3 bucket
echo "Creating S3 bucket..."
if [ "$AWS_REGION" != "us-east-1" ]; then
    aws s3api create-bucket \
        --bucket $BUCKET_NAME \
        --region $AWS_REGION \
        --create-bucket-configuration LocationConstraint=$AWS_REGION
else
    aws s3api create-bucket \
        --bucket $BUCKET_NAME \
        --region $AWS_REGION
fi

# Step 3: Configure bucket settings
echo "Configuring bucket versioning..."
aws s3api put-bucket-versioning \
    --bucket $BUCKET_NAME \
    --versioning-configuration Status=Enabled

echo "Configuring bucket encryption..."
aws s3api put-bucket-encryption \
    --bucket $BUCKET_NAME \
    --server-side-encryption-configuration "{
        \"Rules\": [{
            \"ApplyServerSideEncryptionByDefault\": {
                \"SSEAlgorithm\": \"aws:kms\",
                \"KMSMasterKeyID\": \"$KMS_KEY_ID\"
            },
            \"BucketKeyEnabled\": true
        }]
    }"

echo "Blocking public access..."
aws s3api put-public-access-block \
    --bucket $BUCKET_NAME \
    --public-access-block-configuration \
        BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true

echo "Enabling Transfer Acceleration..."
aws s3api put-bucket-accelerate-configuration \
    --bucket $BUCKET_NAME \
    --accelerate-configuration Status=Enabled

# Step 4: Configure AWS CLI for large file uploads
echo "Configuring AWS CLI for optimal large file transfers..."
aws configure set default.s3.max_concurrent_requests 40
aws configure set default.s3.multipart_threshold 64MB
aws configure set default.s3.multipart_chunksize 64MB

# Step 5: Create folder structure
echo "Creating S3 folder structure..."
echo "" | aws s3 cp - s3://$BUCKET_NAME/$RAW_PREFIX.keep
echo "" | aws s3 cp - s3://$BUCKET_NAME/$KB_PREFIX.keep

# Output configuration
echo "==================================="
echo "AWS Setup Complete!"
echo "==================================="
echo "Save these values for later use:"
echo "BUCKET_NAME=$BUCKET_NAME"
echo "KMS_KEY_ID=$KMS_KEY_ID"
echo "KMS_KEY_ALIAS=$KMS_KEY_ALIAS"
echo "RAW_DATA_PATH=s3://$BUCKET_NAME/$RAW_PREFIX"
echo "KB_DATA_PATH=s3://$BUCKET_NAME/$KB_PREFIX"
echo ""
echo "Next steps:"
echo "1. Upload raw files to s3://$BUCKET_NAME/$RAW_PREFIX"
echo "2. Process and split large files into ≤50MB chunks"
echo "3. Store processed files in s3://$BUCKET_NAME/$KB_PREFIX"
echo "4. Create Bedrock Knowledge Base using the KB path"