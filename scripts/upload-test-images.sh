#!/bin/bash

# Image AI Pipeline - Upload Test Images
# Downloads sample images and uploads to S3 for testing

set -e

echo "📤 Image AI Pipeline - Upload Test Images"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Get S3 bucket from deployment info or parameter
if [ -f "deployment-info.txt" ]; then
    BUCKET=$(grep "Images Bucket:" deployment-info.txt | cut -d' ' -f3)
else
    echo "Enter S3 bucket name:"
    read BUCKET
fi

if [ -z "$BUCKET" ]; then
    echo -e "${RED}❌ S3 bucket not set${NC}"
    exit 1
fi

echo "S3 Bucket: $BUCKET"
echo ""

# Create temp directory
TEMP_DIR="test-images"
mkdir -p $TEMP_DIR

echo "📥 Step 1: Downloading sample images..."
echo ""

# Download sample images from placeholder services
IMAGES=(
    "https://picsum.photos/800/600?random=1"
    "https://picsum.photos/800/600?random=2"
    "https://picsum.photos/800/600?random=3"
    "https://picsum.photos/800/600?random=4"
    "https://picsum.photos/800/600?random=5"
)

for i in "${!IMAGES[@]}"; do
    NUM=$((i+1))
    echo "  Downloading test-image-$NUM.jpg..."
    curl -s -L "${IMAGES[$i]}" -o "$TEMP_DIR/test-image-$NUM.jpg"
done

echo -e "${GREEN}✓${NC} Downloaded 5 sample images"

echo ""
echo "📤 Step 2: Uploading to S3..."
echo ""

# Upload images
for file in $TEMP_DIR/*.jpg; do
    filename=$(basename "$file")
    echo "  Uploading $filename..."
    aws s3 cp "$file" "s3://$BUCKET/test-images/$filename"
done

echo -e "${GREEN}✓${NC} All images uploaded"

echo ""
echo "⏱️  Step 3: Waiting for AI processing..."
echo "  (Rekognition analysis takes ~5-10 seconds per image)"
echo ""

# Wait 30 seconds for processing
for i in {30..1}; do
    echo -ne "  Waiting... $i seconds\r"
    sleep 1
done
echo ""

echo -e "${GREEN}✓${NC} Processing should be complete"

echo ""
echo "========================================="
echo "✅ TEST IMAGES UPLOADED!"
echo "========================================="
echo ""
echo "📊 What happens next:"
echo ""
echo "1. S3 triggers Lambda function"
echo "2. Lambda calls Rekognition AI"
echo "3. AI analyzes:"
echo "   - Objects & scenes"
echo "   - Faces & emotions"
echo "   - Text (OCR)"
echo "   - Content moderation"
echo "4. Results saved to DynamoDB"
echo ""
echo "🎯 Next Steps:"
echo ""
echo "1. Run dashboard to view results:"
echo "   cd dashboard"
echo "   streamlit run app.py"
echo ""
echo "2. Or test API directly:"
echo "   curl \$API_ENDPOINT/stats"
echo ""
echo "3. Search for images:"
echo "   curl \"\$API_ENDPOINT/search?q=person&limit=10\"
echo ""
echo "========================================="
echo ""

# Clean up
echo -e "${YELLOW}Cleanup: Remove temporary files? (y/n)${NC}"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    rm -rf $TEMP_DIR
    echo -e "${GREEN}✓${NC} Temporary files removed"
fi

echo ""
echo "🎉 Done! Images are being analyzed by AI right now!"
echo ""