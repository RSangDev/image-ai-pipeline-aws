#!/bin/bash

# Configure S3 Event Notifications
# This script adds Lambda triggers to S3 bucket after deployment
# Workaround for CloudFormation circular dependency

set -e

echo "🔗 Configuring S3 Event Notifications..."
echo "========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
PROJECT_NAME=${1:-"image-ai-pipeline"}
AWS_REGION=${AWS_REGION:-"us-east-2"}
STACK_NAME="${PROJECT_NAME}-stack"

# Get stack outputs
echo "📊 Getting stack information..."

BUCKET=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --query 'Stacks[0].Outputs[?OutputKey==`ImagesBucketName`].OutputValue' \
    --output text \
    --region "$AWS_REGION")

LAMBDA_ARN=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --query 'Stacks[0].Outputs[?OutputKey==`ProcessorFunctionName`].OutputValue' \
    --output text \
    --region "$AWS_REGION")

# Get full Lambda ARN
LAMBDA_ARN=$(aws lambda get-function \
    --function-name "$LAMBDA_ARN" \
    --query 'Configuration.FunctionArn' \
    --output text \
    --region "$AWS_REGION")

echo "  Bucket: $BUCKET"
echo "  Lambda: $LAMBDA_ARN"
echo ""

# Create notification configuration JSON
cat > /tmp/s3-notification.json << EOF
{
  "LambdaFunctionConfigurations": [
    {
      "Id": "ImageProcessorJPG",
      "LambdaFunctionArn": "$LAMBDA_ARN",
      "Events": ["s3:ObjectCreated:*"],
      "Filter": {
        "Key": {
          "FilterRules": [
            {
              "Name": "suffix",
              "Value": ".jpg"
            }
          ]
        }
      }
    },
    {
      "Id": "ImageProcessorJPEG",
      "LambdaFunctionArn": "$LAMBDA_ARN",
      "Events": ["s3:ObjectCreated:*"],
      "Filter": {
        "Key": {
          "FilterRules": [
            {
              "Name": "suffix",
              "Value": ".jpeg"
            }
          ]
        }
      }
    },
    {
      "Id": "ImageProcessorPNG",
      "LambdaFunctionArn": "$LAMBDA_ARN",
      "Events": ["s3:ObjectCreated:*"],
      "Filter": {
        "Key": {
          "FilterRules": [
            {
              "Name": "suffix",
              "Value": ".png"
            }
          ]
        }
      }
    }
  ]
}
EOF

echo "🔧 Applying S3 notification configuration..."

aws s3api put-bucket-notification-configuration \
    --bucket "$BUCKET" \
    --notification-configuration file:///tmp/s3-notification.json \
    --region "$AWS_REGION"

echo -e "${GREEN}✓${NC} S3 event notifications configured!"
echo ""
echo "Test it:"
echo "  aws s3 cp test.jpg s3://$BUCKET/"
echo "  (Lambda will be triggered automatically)"
echo ""

# Cleanup
rm /tmp/s3-notification.json