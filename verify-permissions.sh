#!/bin/bash

# Script to verify if permissions have been granted
echo "==================================="
echo "Verifying AWS Permissions"
echo "==================================="

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track if all permissions are granted
ALL_GOOD=true

echo -e "\nChecking current user identity..."
aws sts get-caller-identity

echo -e "\n${YELLOW}Testing S3 Permissions...${NC}"
# Test S3 permissions
TEST_BUCKET="jim-ai-forensic-test-$RANDOM"

# Test CreateBucket
echo -n "Testing s3:CreateBucket... "
if aws s3api create-bucket --bucket $TEST_BUCKET --region us-east-1 2>/dev/null; then
    echo -e "${GREEN}✓ Granted${NC}"
    # Clean up test bucket
    aws s3api delete-bucket --bucket $TEST_BUCKET 2>/dev/null
else
    echo -e "${RED}✗ Not granted${NC}"
    ALL_GOOD=false
fi

# Test ListBuckets
echo -n "Testing s3:ListAllMyBuckets... "
if aws s3api list-buckets 2>/dev/null 1>/dev/null; then
    echo -e "${GREEN}✓ Granted${NC}"
else
    echo -e "${RED}✗ Not granted${NC}"
    ALL_GOOD=false
fi

echo -e "\n${YELLOW}Testing KMS Permissions...${NC}"
# Test KMS permissions
echo -n "Testing kms:ListKeys... "
if aws kms list-keys --region us-east-1 2>/dev/null 1>/dev/null; then
    echo -e "${GREEN}✓ Granted${NC}"
else
    echo -e "${RED}✗ Not granted${NC}"
    ALL_GOOD=false
fi

echo -e "\n${YELLOW}Testing Bedrock Permissions...${NC}"
# Test Bedrock permissions
echo -n "Testing bedrock:ListFoundationModels... "
if aws bedrock list-foundation-models --region us-east-1 2>/dev/null 1>/dev/null; then
    echo -e "${GREEN}✓ Granted${NC}"
else
    echo -e "${RED}✗ Not granted${NC}"
    ALL_GOOD=false
fi

echo -e "\n${YELLOW}Testing Lambda Permissions...${NC}"
# Test Lambda permissions
echo -n "Testing lambda:ListFunctions... "
if aws lambda list-functions --region us-east-1 2>/dev/null 1>/dev/null; then
    echo -e "${GREEN}✓ Granted${NC}"
else
    echo -e "${RED}✗ Not granted${NC}"
    ALL_GOOD=false
fi

echo -e "\n${YELLOW}Testing OpenSearch Serverless Permissions...${NC}"
# Test OpenSearch Serverless permissions
echo -n "Testing aoss:ListCollections... "
if aws opensearchserverless list-collections --region us-east-1 2>/dev/null 1>/dev/null; then
    echo -e "${GREEN}✓ Granted${NC}"
else
    echo -e "${RED}✗ Not granted${NC}"
    ALL_GOOD=false
fi

echo -e "\n==================================="
if [ "$ALL_GOOD" = true ]; then
    echo -e "${GREEN}✓ All permissions granted!${NC}"
    echo "You can now run ./aws-setup.sh to set up your infrastructure."
else
    echo -e "${RED}✗ Some permissions are missing.${NC}"
    echo "Please share required-iam-policy.json with your AWS administrator."
    echo ""
    echo "Files to share with admin:"
    echo "1. required-iam-policy.json - The IAM policy to attach"
    echo "2. permission-request-email.md - Email template explaining the request"
fi
echo "==================================="