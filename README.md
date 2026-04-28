# 🖼️ Image AI Processing Pipeline

**AI-powered image analysis using AWS Rekognition** - Upload images and get instant AI insights on objects, faces, text, and content moderation.

![AWS](https://img.shields.io/badge/AWS-Free_Tier-orange?logo=amazon-aws)
![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![Serverless](https://img.shields.io/badge/Architecture-Serverless-green)
![AI](https://img.shields.io/badge/AI-Rekognition-purple)
![Cost](https://img.shields.io/badge/Cost-$0--2/month-success)

---

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [AWS Services](#-aws-services-used)
- [AI Capabilities](#-ai-capabilities)
- [Cost Breakdown](#-cost-breakdown)
- [Prerequisites](#-prerequisites)
- [Quick Start](#-quick-start)
- [Usage](#-usage)
- [Dashboard](#-dashboard)
- [API Documentation](#-api-documentation)
- [Troubleshooting](#-troubleshooting)

---

## ✨ Features

- **🤖 AI Image Analysis** - Automatic detection of objects, scenes, activities
- **👤 Face Detection** - Age, gender, emotions, facial attributes
- **📝 Text Extraction (OCR)** - Read text from images
- **🚨 Content Moderation** - Flag inappropriate content automatically
- **⭐ Celebrity Recognition** - Identify famous people
- **🔍 Smart Search** - Search images by labels, faces, text
- **📊 Interactive Dashboard** - Streamlit web interface
- **🔔 Real-time Alerts** - SNS notifications for flagged content
- **💰 Cost Optimized** - 100% Free Tier eligible

---

## 🏗️ Architecture

```
┌─────────────┐
│   Upload    │
│   Image     │
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│   S3 Bucket         │ ← Image storage (5GB FREE)
│   (Event trigger)   │
└──────┬──────────────┘
       │ S3 Event
       ▼
┌─────────────────────┐
│   Lambda Processor  │ ← Image analysis (1M invocations FREE)
│   (Python 3.11)     │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  AWS Rekognition    │ ← AI/ML Vision API (5k images/month FREE)
│  - Detect Labels    │
│  - Detect Faces     │
│  - Detect Text      │
│  - Moderation       │
│  - Celebrities      │
└──────┬──────────────┘
       │
       ├─────────────────────┐
       ▼                     ▼
┌─────────────┐      ┌─────────────┐
│  DynamoDB   │      │  SNS Topic  │
│  (Metadata) │      │  (Alerts)   │
│  25GB FREE  │      │             │
└──────┬──────┘      └─────────────┘
       │
       ▼
┌─────────────────────┐
│   API Gateway       │ ← Search API (1M requests FREE)
│   /search           │
│   /image/{id}       │
│   /stats            │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  Streamlit          │ ← Interactive Dashboard
│  Dashboard          │
└─────────────────────┘
```

---

## 🛠️ AWS Services Used

| Service | Purpose | Free Tier Limit | Your Usage |
|---------|---------|----------------|------------|
| **S3** | Image storage | 5GB | ~1-2GB ✅ |
| **Lambda** | Event processing | 1M requests/month | ~10k ✅ |
| **Rekognition** | AI image analysis | 5k images/month | ~100-500 ✅ |
| **DynamoDB** | Metadata storage | 25GB | ~500MB ✅ |
| **API Gateway** | REST API | 1M calls/month | ~5k ✅ |
| **SNS** | Alerts | 1M publishes/month | ~10 ✅ |
| **CloudWatch** | Logging | 5GB logs/month | ~200MB ✅ |

**Total Monthly Cost: $0-2** 💰

---

## 🤖 AI Capabilities

### 1. Object & Scene Detection
- Identifies 1000+ object categories
- Detects scenes (beach, forest, city)
- Recognizes activities (playing, running, eating)
- Confidence scores for each label

### 2. Face Analysis
- Face detection and counting
- Age range estimation
- Gender prediction
- Emotion detection (happy, sad, angry, surprised, etc.)
- Facial attributes (smile, eyeglasses, beard, etc.)

### 3. Text Extraction (OCR)
- Reads printed text from images
- Supports multiple languages
- Detects text orientation
- Line and word-level detection

### 4. Content Moderation
- Detects inappropriate content
- Categories: Explicit Nudity, Suggestive, Violence, Visually Disturbing
- Automatic alerts via SNS
- Confidence-based flagging

### 5. Celebrity Recognition
- Identifies famous people
- Provides celebrity name and URLs
- Match confidence scores

---

## 💰 Cost Breakdown

### Free Tier (First 12 months)

✅ **Rekognition**
- 5,000 images/month FREE
- **Your usage:** ~100-500 images = **FREE**

✅ **S3**
- 5GB storage FREE
- **Your usage:** ~1-2GB = **FREE**

✅ **Lambda**
- 1M requests/month FREE
- **Your usage:** ~10k requests = **FREE**

✅ **DynamoDB**
- 25GB storage FREE
- **Your usage:** ~500MB = **FREE**

### After Free Tier

Estimated cost with 500 images/month: **~$2/month**

- Rekognition: $0.50 (after 5k free)
- S3: $0.50
- Lambda: $0.20
- DynamoDB: $0.50
- API Gateway: $0.30

---

## 📚 Prerequisites

### Required
- **AWS Account** (Free Tier eligible)
- **AWS CLI** installed and configured
- **Python 3.11+** (for local testing)
- **Git** (for version control)

### Installation

**AWS CLI:**
```bash
# Windows
winget install Amazon.AWSCLI

# Mac
brew install awscli

# Linux
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```

**Configure AWS:**
```bash
aws configure
# AWS Access Key ID: YOUR_KEY
# AWS Secret Access Key: YOUR_SECRET
# Default region: us-east-2
# Default output format: json
```

---

## 🚀 Quick Start

### Option 1: Automated Deploy (Recommended)

**Windows (PowerShell):**
```powershell
# Clone repository
git clone https://github.com/RSangDev/image-ai-pipeline-aws.git
cd image-ai-pipeline-aws

# Deploy everything
.\scripts\deploy.ps1

# Wait ~3-4 minutes for deployment
# Copy API endpoint and S3 bucket from output
```

**Mac/Linux (Bash):**
```bash
# Clone repository
git clone https://github.com/RSangDev/image-ai-pipeline-aws.git
cd image-ai-pipeline-aws

# Make scripts executable
chmod +x scripts/*.sh

# Deploy everything
./scripts/deploy.sh

# Wait ~3-4 minutes for deployment
# Copy API endpoint and S3 bucket from output
```

### Option 2: Manual Deploy

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed manual steps.

---

## 📖 Usage

### 1. Upload Images

**Via AWS CLI:**
```bash
aws s3 cp your-image.jpg s3://YOUR-BUCKET-NAME/
```

**Via Dashboard:**
1. Run dashboard: `streamlit run dashboard/app.py`
2. Enter API endpoint and S3 bucket in sidebar
3. Use upload widget

**Via Script (Test Images):**
```bash
./scripts/upload-test-images.sh
```

### 2. View Results

**Dashboard:**
```bash
cd dashboard
pip install -r requirements.txt
streamlit run app.py

# Opens at http://localhost:8501
```

**API:**
```bash
# Search images
curl "$API_ENDPOINT/search?q=dog&limit=10"

# Get statistics
curl "$API_ENDPOINT/stats"

# Get specific image
curl "$API_ENDPOINT/image/{image_id}"
```

---

## 📊 Dashboard

The Streamlit dashboard provides:

### Features
- 🔍 **Search** - Search by labels, faces, text
- 📊 **Statistics** - View pipeline metrics
- 🏷️ **Browse** - Browse by common labels
- 📤 **Upload** - Upload new images
- 🔎 **Details** - View full AI analysis

### Screenshots

*(Add screenshots here after deployment)*

---

## 🔌 API Documentation

### Base URL
```
https://tl22hztl73.execute-api.us-east-2.amazonaws.com/prod/health
```

### Endpoints

#### 1. Search Images
```http
GET /search?q={query}&faces={true|false}&text={true|false}&limit={number}
```

**Parameters:**
- `q` (optional) - Search query (label name)
- `faces` (optional) - Filter images with faces
- `text` (optional) - Filter images with text
- `limit` (optional) - Max results (default: 20)

**Response:**
```json
{
  "results": [
    {
      "image_id": "uuid",
      "url": "signed-s3-url",
      "upload_date": "2024-01-01T12:00:00",
      "labels": ["dog", "pet", "animal"],
      "face_count": 0,
      "has_text": false,
      "file_size": 245678
    }
  ],
  "count": 10
}
```

#### 2. Get Image Details
```http
GET /image/{image_id}
```

**Response:**
```json
{
  "image_id": "uuid",
  "url": "signed-s3-url",
  "labels": [
    {"name": "Dog", "confidence": 98.5, "categories": ["Animals"]}
  ],
  "faces": [
    {
      "age_range": "25-35",
      "gender": "Male",
      "emotions": [
        {"type": "HAPPY", "confidence": 95.2}
      ]
    }
  ],
  "text": [
    {"text": "Hello World", "confidence": 99.1}
  ],
  "celebrities": [],
  "moderation_labels": []
}
```

#### 3. Get Statistics
```http
GET /stats
```

**Response:**
```json
{
  "total_images": 150,
  "total_faces_detected": 87,
  "images_with_text": 23,
  "images_with_celebrities": 5,
  "flagged_images": 2,
  "top_labels": [
    {"label": "Person", "count": 45},
    {"label": "Car", "count": 32}
  ]
}
```

---

## 🐛 Troubleshooting

### Issue: "Access Denied" when uploading to S3

**Solution:**
```bash
# Check AWS credentials
aws sts get-caller-identity

# Ensure your IAM user has S3 permissions
```

### Issue: Images uploaded but no analysis results

**Solution:**
1. Check CloudWatch logs: `/aws/lambda/image-ai-pipeline-processor`
2. Verify S3 event notification is configured
3. Ensure Lambda has Rekognition permissions

### Issue: "Rekognition limit exceeded"

**Solution:**
- Free Tier: 5,000 images/month
- Check usage: AWS Console → Rekognition → Billing
- Wait for next month or upgrade

### Issue: Dashboard shows "API Error"

**Solution:**
1. Verify API endpoint is correct
2. Check CORS is enabled
3. Test API directly: `curl $API_ENDPOINT/stats`

---

## 🎯 Use Cases

- **Photo Library Management** - Auto-tag and organize photos
- **Content Moderation** - Flag inappropriate uploads
- **Document Processing** - Extract text from scanned documents
- **Face Recognition** - Attendance systems, security
- **Celebrity Tracking** - Media monitoring
- **Accessibility** - Generate alt-text for images
- **E-commerce** - Auto-categorize product images

---

## 🚧 Roadmap

- [ ] Video analysis support
- [ ] Batch upload via UI
- [ ] Custom labels training
- [ ] Face comparison/matching
- [ ] Advanced search filters
- [ ] Export to CSV/Excel
- [ ] Multi-user authentication
- [ ] Image similarity search

---

## 📝 License

MIT License - See [LICENSE](LICENSE) file

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

---

## 📧 Contact

Questions? Issues? Suggestions?

- **GitHub Issues:** [Open an issue](https://github.com/RSangDev/image-ai-pipeline-aws/issues)
- **Email:** your.email@example.com

---

## ⭐ Show Your Support

If this project helped you, give it a ⭐ on GitHub!

---

**Built with ❤️ using AWS Free Tier**

*AI-powered image processing, zero cost! 🚀*