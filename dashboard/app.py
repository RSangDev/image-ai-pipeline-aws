"""
Image AI Pipeline - Streamlit Dashboard
Upload, search, and visualize AI-analyzed images
"""

import streamlit as st
import requests
import boto3
import json
from datetime import datetime
import os

# Page config
st.set_page_config(
    page_title="Image AI Pipeline",
    page_icon="🖼️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .stMetric {
        background-color: #1e1e1e;
        padding: 15px;
        border-radius: 8px;
    }
    .image-card {
        border: 1px solid #333;
        border-radius: 8px;
        padding: 10px;
        margin: 10px 0;
    }
    </style>
""", unsafe_allow_html=True)

# Session state
if 'api_endpoint' not in st.session_state:
    st.session_state.api_endpoint = ""
if 's3_bucket' not in st.session_state:
    st.session_state.s3_bucket = ""

# Sidebar Configuration
with st.sidebar:
    st.title("⚙️ Configuration")
    
    # API Endpoint
    api_endpoint = st.text_input(
        "API Gateway Endpoint",
        value=st.session_state.api_endpoint,
        placeholder="https://xxx.execute-api.region.amazonaws.com/prod",
        help="Get from CloudFormation outputs"
    )
    
    if api_endpoint != st.session_state.api_endpoint:
        st.session_state.api_endpoint = api_endpoint
    
    # S3 Bucket
    s3_bucket = st.text_input(
        "S3 Bucket Name",
        value=st.session_state.s3_bucket,
        placeholder="image-ai-pipeline-images-xxxxx",
        help="Get from CloudFormation outputs"
    )
    
    if s3_bucket != st.session_state.s3_bucket:
        st.session_state.s3_bucket = s3_bucket
    
    st.divider()
    
    # Upload Image
    st.subheader("📤 Upload Image")
    uploaded_file = st.file_uploader(
        "Choose an image",
        type=['jpg', 'jpeg', 'png', 'gif'],
        help="Upload will trigger AI analysis automatically"
    )
    
    if uploaded_file and st.session_state.s3_bucket:
        if st.button("🚀 Upload & Analyze", use_container_width=True):
            with st.spinner("Uploading to S3..."):
                try:
                    # Upload to S3
                    s3 = boto3.client('s3')
                    filename = f"uploads/{uploaded_file.name}"
                    s3.upload_fileobj(
                        uploaded_file,
                        st.session_state.s3_bucket,
                        filename
                    )
                    st.success(f"✅ Uploaded! AI analysis in progress...")
                    st.info("⏱️ Wait ~10 seconds, then search to see results")
                except Exception as e:
                    st.error(f"❌ Upload failed: {str(e)}")
                    st.info("Make sure AWS credentials are configured: `aws configure`")

# Main content
st.title("🖼️ Image AI Pipeline Dashboard")
st.markdown("**Powered by AWS Rekognition** - Computer Vision at scale")

# Check configuration
if not st.session_state.api_endpoint:
    st.warning("⚠️ Configure API endpoint in sidebar to get started")
    st.info("""
    **Quick Start:**
    1. Deploy the CloudFormation stack
    2. Copy API endpoint and S3 bucket from outputs
    3. Paste them in the sidebar
    4. Upload images and search! 🚀
    """)
    st.stop()

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["🔍 Search", "📊 Statistics", "🏷️ Browse by Label", "ℹ️ About"])

# Tab 1: Search
with tab1:
    st.subheader("🔍 Search Images")
    
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        search_query = st.text_input(
            "Search by label, object, or scene",
            placeholder="dog, beach, car, sunset...",
            help="Search for objects, scenes, activities detected by AI"
        )
    
    with col2:
        has_faces = st.checkbox("👤 Has Faces")
    
    with col3:
        has_text = st.checkbox("📝 Has Text")
    
    limit = st.slider("Max results", 5, 50, 20)
    
    if st.button("🔎 Search", use_container_width=True) or search_query:
        with st.spinner("Searching..."):
            try:
                # Build query params
                params = {'limit': limit}
                if search_query:
                    params['q'] = search_query.lower()
                if has_faces:
                    params['faces'] = 'true'
                if has_text:
                    params['text'] = 'true'
                
                # Call API
                response = requests.get(
                    f"{st.session_state.api_endpoint}/search",
                    params=params,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get('results', [])
                    
                    st.success(f"Found {len(results)} images")
                    
                    if results:
                        # Display in grid
                        cols_per_row = 3
                        for i in range(0, len(results), cols_per_row):
                            cols = st.columns(cols_per_row)
                            for j, col in enumerate(cols):
                                if i + j < len(results):
                                    result = results[i + j]
                                    with col:
                                        # Image
                                        st.image(result['url'], use_container_width=True)
                                        
                                        # Metadata
                                        st.caption(f"**Labels:** {', '.join(result['labels'][:3])}")
                                        st.caption(f"👤 Faces: {result['face_count']} | 📝 Text: {'Yes' if result['has_text'] else 'No'}")
                                        st.caption(f"📅 {result['upload_date'][:10]}")
                                        
                                        # View details button
                                        if st.button(f"View Details", key=f"view_{result['image_id']}"):
                                            st.session_state.selected_image = result['image_id']
                    else:
                        st.info("No images found. Try a different search term.")
                else:
                    st.error(f"API Error: {response.status_code}")
                    
            except Exception as e:
                st.error(f"Error: {str(e)}")

# Tab 2: Statistics
with tab2:
    st.subheader("📊 Pipeline Statistics")
    
    if st.button("🔄 Refresh Stats", use_container_width=True):
        with st.spinner("Loading statistics..."):
            try:
                response = requests.get(
                    f"{st.session_state.api_endpoint}/stats",
                    timeout=10
                )
                
                if response.status_code == 200:
                    stats = response.json()
                    
                    # Metrics
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("📸 Total Images", f"{stats.get('total_images', 0):,}")
                    
                    with col2:
                        st.metric("👤 Faces Detected", f"{stats.get('total_faces_detected', 0):,}")
                    
                    with col3:
                        st.metric("📝 With Text", stats.get('images_with_text', 0))
                    
                    with col4:
                        st.metric("⭐ Celebrities", stats.get('images_with_celebrities', 0))
                    
                    # Warning for flagged content
                    if stats.get('flagged_images', 0) > 0:
                        st.warning(f"⚠️ {stats['flagged_images']} images flagged for moderation")
                    
                    st.divider()
                    
                    # Top labels
                    st.subheader("🏷️ Most Common Labels")
                    top_labels = stats.get('top_labels', [])
                    
                    if top_labels:
                        import pandas as pd
                        import plotly.express as px
                        
                        df = pd.DataFrame(top_labels)
                        
                        fig = px.bar(
                            df,
                            x='count',
                            y='label',
                            orientation='h',
                            title='Top 10 Detected Labels',
                            labels={'count': 'Count', 'label': 'Label'},
                            color='count',
                            color_continuous_scale='viridis'
                        )
                        fig.update_layout(
                            showlegend=False,
                            height=400,
                            yaxis={'categoryorder': 'total ascending'}
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No data yet. Upload some images first!")
                else:
                    st.error(f"API Error: {response.status_code}")
                    
            except Exception as e:
                st.error(f"Error: {str(e)}")

# Tab 3: Browse by Label
with tab3:
    st.subheader("🏷️ Browse by Common Labels")
    
    common_labels = [
        "person", "car", "building", "tree", "dog", "cat",
        "beach", "food", "nature", "sky", "mountain", "water"
    ]
    
    selected_label = st.selectbox("Select a label", common_labels)
    
    if st.button("View Images", use_container_width=True):
        with st.spinner(f"Loading {selected_label} images..."):
            try:
                response = requests.get(
                    f"{st.session_state.api_endpoint}/search",
                    params={'label': selected_label, 'limit': 12},
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get('results', [])
                    
                    if results:
                        st.success(f"Found {len(results)} images with '{selected_label}'")
                        
                        # Grid display
                        cols = st.columns(3)
                        for i, result in enumerate(results):
                            with cols[i % 3]:
                                st.image(result['url'], use_container_width=True)
                                st.caption(f"**{', '.join(result['labels'][:3])}**")
                    else:
                        st.info(f"No images found with label '{selected_label}'")
                else:
                    st.error(f"API Error: {response.status_code}")
                    
            except Exception as e:
                st.error(f"Error: {str(e)}")

# Tab 4: About
with tab4:
    st.subheader("ℹ️ About This Project")
    
    st.markdown("""
    ### 🎯 What is this?
    
    An **AI-powered image processing pipeline** built with AWS serverless services.
    
    ### 🏗️ Architecture
    
    ```
    Upload Image → S3 → Lambda → Rekognition AI
                                      ↓
                                 DynamoDB
                                      ↓
                              Search API + Dashboard
    ```
    
    ### 🤖 AI Capabilities
    
    - **Object Detection** - Identifies objects, scenes, activities
    - **Face Analysis** - Detects faces, emotions, age, gender
    - **Text Extraction (OCR)** - Reads text from images
    - **Content Moderation** - Flags inappropriate content
    - **Celebrity Recognition** - Identifies famous people
    
    ### 🛠️ AWS Services Used
    
    - **S3** - Image storage
    - **Lambda** - Serverless processing
    - **Rekognition** - AI/ML vision API
    - **DynamoDB** - Metadata database
    - **API Gateway** - REST API
    - **SNS** - Alerts
    - **CloudFormation** - Infrastructure as Code
    
    ### 💰 Cost
    
    **~$0-2/month** with moderate usage
    - Rekognition: 5,000 images/month FREE
    - S3: 5GB storage FREE
    - Lambda: 1M requests FREE
    
    ### 📚 Learn More
    
    - [GitHub Repository](#)
    - [AWS Rekognition Docs](https://docs.aws.amazon.com/rekognition/)
    - [API Documentation](#)
    """)
    
    st.divider()
    
    st.info("""
    **💡 Pro Tip:**
    Upload various types of images (people, nature, text, objects) to see 
    the full power of AI image analysis!
    """)

# Footer
st.divider()
st.markdown("""
    <div style='text-align: center; color: gray; padding: 20px;'>
        <p>🚀 Image AI Pipeline • Powered by AWS Free Tier</p>
        <p style='font-size: 0.9em;'>S3 + Lambda + Rekognition + DynamoDB + API Gateway</p>
    </div>
""", unsafe_allow_html=True)

# Show selected image details in modal (if any)
if 'selected_image' in st.session_state:
    with st.expander("🔍 Image Details", expanded=True):
        try:
            response = requests.get(
                f"{st.session_state.api_endpoint}/image/{st.session_state.selected_image}",
                timeout=10
            )
            
            if response.status_code == 200:
                img_data = response.json()
                
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.image(img_data['url'], use_container_width=True)
                
                with col2:
                    st.subheader("📋 Metadata")
                    st.write(f"**Image ID:** `{img_data['image_id']}`")
                    st.write(f"**Upload Date:** {img_data['upload_date']}")
                    st.write(f"**File Size:** {img_data['file_size']:,} bytes")
                    
                    st.subheader("🏷️ Labels")
                    for label in img_data['labels'][:10]:
                        st.write(f"- {label['name']} ({label['confidence']}%)")
                    
                    if img_data['faces']:
                        st.subheader("👤 Faces Detected")
                        for i, face in enumerate(img_data['faces'][:3]):
                            st.write(f"**Face {i+1}:**")
                            st.write(f"- Age: {face['age_range']}")
                            st.write(f"- Gender: {face['gender']}")
                            st.write(f"- Emotions: {', '.join([e['type'] for e in face['emotions']])}")
                    
                    if img_data['text']:
                        st.subheader("📝 Text Detected")
                        for text in img_data['text']:
                            st.write(f"- {text['text']} ({text['confidence']}%)")
                    
                    if img_data['celebrities']:
                        st.subheader("⭐ Celebrities")
                        for celeb in img_data['celebrities']:
                            st.write(f"- {celeb['name']} ({celeb['confidence']}%)")
        except:
            pass
        
        if st.button("Close"):
            del st.session_state.selected_image
            st.rerun()