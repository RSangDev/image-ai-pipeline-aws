#!/bin/bash

# Image AI Pipeline - Deploy Script (Bash)
# Deploys complete CloudFormation stack

set -e

echo "🚀 Image AI Pipeline - Deployment Script"
echo "========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
PROJECT_NAME=${1:-"image-ai-pipeline"}
AWS_REGION=${AWS_REGION:-"us-east-2"}
STACK_NAME="${PROJECT_NAME}-stack"

echo "📋 Configuration:"
echo "  Project Name: $PROJECT_NAME"
echo "  AWS Region: $AWS_REGION"
echo "  Stack Name: $STACK_NAME"
echo ""

# Check AWS CLI
echo "🔍 Checking prerequisites..."
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI not found${NC}"
    exit 1
fi
echo -e "${GREEN}✓${NC} AWS CLI installed"

# Check credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ AWS credentials not configured${NC}"
    exit 1
fi
echo -e "${GREEN}✓${NC} AWS credentials configured"

AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo -e "${GREEN}✓${NC} AWS Account: $AWS_ACCOUNT_ID"

echo ""
echo "📦 Step 1: Packaging Lambda functions..."

# Package image-processor
echo "  Packaging image-processor..."
cd lambda/image-processor
rm -f function.zip
zip -q function.zip handler.py
cd ../..

# Package image-search
echo "  Packaging image-search..."
cd lambda/image-search
rm -f function.zip
zip -q function.zip handler.py
cd ../..

# Package content-moderation
echo "  Packaging content-moderation..."
cd lambda/content-moderation
rm -f function.zip
zip -q function.zip handler.py
cd ../..

echo -e "${GREEN}✓${NC} Lambda functions packaged"

echo ""
echo "☁️  Step 2: Creating deployment bucket..."

DEPLOYMENT_BUCKET="${PROJECT_NAME}-deploy-$(date +%s)"

if aws s3 mb "s3://$DEPLOYMENT_BUCKET" --region "$AWS_REGION" 2>&1 | grep -q 'BucketAlreadyOwnedByYou\|make_bucket:'; then
    echo -e "${GREEN}✓${NC} Deployment bucket created: $DEPLOYMENT_BUCKET"
else
    echo -e "${YELLOW}⚠${NC} Bucket creation warning (may already exist)"
fi

echo ""
echo "📤 Step 3: Packaging CloudFormation template..."

aws cloudformation package \
    --template-file cloudformation/template.yaml \
    --s3-bucket "$DEPLOYMENT_BUCKET" \
    --output-template-file packaged-template.yaml \
    --region "$AWS_REGION" > /dev/null

echo -e "${GREEN}✓${NC} Template packaged"

echo ""
echo "🚀 Step 4: Deploying CloudFormation stack..."
echo "  This may take 3-4 minutes..."

aws cloudformation deploy \
    --template-file packaged-template.yaml \
    --stack-name "$STACK_NAME" \
    --capabilities CAPABILITY_IAM \
    --parameter-overrides ProjectName="$PROJECT_NAME" \
    --region "$AWS_REGION"

echo -e "${GREEN}✓${NC} Stack deployed"

echo ""
echo "🔄 Step 5: Updating Lambda function codes..."

# Get function names
PROCESSOR_FUNCTION=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --query 'Stacks[0].Outputs[?OutputKey==`ProcessorFunctionName`].OutputValue' \
    --output text \
    --region "$AWS_REGION")

SEARCH_FUNCTION=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --query 'Stacks[0].Outputs[?OutputKey==`SearchFunctionName`].OutputValue' \
    --output text \
    --region "$AWS_REGION")

# Update functions
echo "  Updating image-processor..."
aws lambda update-function-code \
    --function-name "$PROCESSOR_FUNCTION" \
    --zip-file fileb://lambda/image-processor/function.zip \
    --region "$AWS_REGION" > /dev/null

echo "  Updating image-search..."
aws lambda update-function-code \
    --function-name "$SEARCH_FUNCTION" \
    --zip-file fileb://lambda/image-search/function.zip \
    --region "$AWS_REGION" > /dev/null

echo -e "${GREEN}✓${NC} Lambda functions updated"

echo ""
echo "📊 Step 6: Retrieving outputs..."

OUTPUTS=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --query 'Stacks[0].Outputs' \
    --region "$AWS_REGION")

API_ENDPOINT=$(echo "$OUTPUTS" | grep -A1 "ApiEndpoint" | grep "OutputValue" | cut -d'"' -f4)
IMAGES_BUCKET=$(echo "$OUTPUTS" | grep -A1 "ImagesBucketName" | grep "OutputValue" | cut -d'"' -f4)

echo ""
echo "========================================="
echo "✅ DEPLOYMENT SUCCESSFUL!"
echo "========================================="
echo ""
echo "📌 Stack Outputs:"
echo ""
echo "  API Endpoint:"
echo -e "    ${GREEN}$API_ENDPOINT${NC}"
echo ""
echo "  Images S3 Bucket:"
echo "    $IMAGES_BUCKET"
echo ""
echo "  Processor Function:"
echo "    $PROCESSOR_FUNCTION"
echo ""
echo "  Search Function:"
echo "    $SEARCH_FUNCTION"
echo ""
echo "========================================="
echo ""
echo "🧪 Next Steps:"
echo ""
echo "1. Upload test images:"
echo "   aws s3 cp your-image.jpg s3://$IMAGES_BUCKET/"
echo ""
echo "2. Run dashboard:"
echo "   cd dashboard"
echo "   pip install -r requirements.txt"
echo "   streamlit run app.py"
echo ""
echo "3. Configure dashboard:"
echo -e "   API Endpoint: ${GREEN}$API_ENDPOINT${NC}"
echo "   S3 Bucket: $IMAGES_BUCKET"
echo ""
echo "========================================="
echo ""

# Save deployment info
cat > deployment-info.txt << EOF
Image AI Pipeline - Deployment Info
====================================

Deployed: $(date)
Stack Name: $STACK_NAME
AWS Region: $AWS_REGION
AWS Account: $AWS_ACCOUNT_ID

API Endpoint: $API_ENDPOINT
Images Bucket: $IMAGES_BUCKET
Processor Function: $PROCESSOR_FUNCTION
Search Function: $SEARCH_FUNCTION

Upload Command:
aws s3 cp your-image.jpg s3://$IMAGES_BUCKET/

Dashboard Config:
- API Endpoint: $API_ENDPOINT
- S3 Bucket: $IMAGES_BUCKET

Rekognition Info:
- Free Tier: 5,000 images/month
- After: \$0.001 per image
- Features: Labels, Faces, Text, Moderation, Celebrities
EOF

echo -e "${GREEN}✓${NC} Deployment info saved to: deployment-info.txt"
echo ""