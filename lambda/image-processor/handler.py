"""
Image AI Processing Pipeline - Main Processor
Triggers on S3 upload, analyzes with Rekognition, saves metadata to DynamoDB
"""

import json
import boto3
import os
from datetime import datetime
from urllib.parse import unquote_plus
from decimal import Decimal
import uuid

# AWS Clients
s3 = boto3.client('s3')
rekognition = boto3.client('rekognition')
dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')

# Environment variables
METADATA_TABLE = os.environ.get('METADATA_TABLE', 'image-metadata')
ALERT_TOPIC_ARN = os.environ.get('ALERT_TOPIC_ARN', '')


def convert_floats_to_decimal(obj):
    """
    Recursively convert all float values to Decimal for DynamoDB
    """
    if isinstance(obj, list):
        return [convert_floats_to_decimal(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: convert_floats_to_decimal(value) for key, value in obj.items()}
    elif isinstance(obj, float):
        return Decimal(str(obj))
    else:
        return obj


def lambda_handler(event, context):
    """
    Triggered by S3 upload event
    Analyzes image with Rekognition and stores metadata
    """
    print(f"Event: {json.dumps(event)}")
    
    try:
        # Get S3 event details
        for record in event['Records']:
            bucket = record['s3']['bucket']['name']
            key = unquote_plus(record['s3']['object']['key'])
            
            print(f"Processing image: s3://{bucket}/{key}")
            
            # Skip if not an image
            if not is_image(key):
                print(f"Skipping non-image file: {key}")
                continue
            
            # Generate unique image ID
            image_id = str(uuid.uuid4())
            
            # Analyze image with Rekognition
            analysis = analyze_image(bucket, key)
            
            # Check for inappropriate content
            if has_inappropriate_content(analysis):
                send_moderation_alert(bucket, key, analysis['moderation_labels'])
            
            # Save metadata to DynamoDB
            save_metadata(image_id, bucket, key, analysis)
            
            print(f"✓ Image processed successfully: {image_id}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Images processed successfully'})
        }
        
    except Exception as e:
        print(f"Error processing image: {str(e)}")
        raise


def is_image(filename):
    """Check if file is an image"""
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
    return any(filename.lower().endswith(ext) for ext in image_extensions)


def analyze_image(bucket, key):
    """
    Analyze image using AWS Rekognition
    Returns comprehensive analysis including labels, faces, text, moderation
    """
    analysis = {
        'labels': [],
        'faces': [],
        'text': [],
        'moderation_labels': [],
        'celebrities': []
    }
    
    try:
        # Detect labels (objects, scenes, activities)
        labels_response = rekognition.detect_labels(
            Image={'S3Object': {'Bucket': bucket, 'Name': key}},
            MaxLabels=20,
            MinConfidence=70
        )
        analysis['labels'] = [
            {
                'name': label['Name'],
                'confidence': round(label['Confidence'], 2),
                'categories': [cat['Name'] for cat in label.get('Categories', [])]
            }
            for label in labels_response['Labels']
        ]
        
        # Detect faces
        faces_response = rekognition.detect_faces(
            Image={'S3Object': {'Bucket': bucket, 'Name': key}},
            Attributes=['ALL']
        )
        analysis['faces'] = [
            {
                'age_range': f"{face['AgeRange']['Low']}-{face['AgeRange']['High']}",
                'gender': face['Gender']['Value'],
                'emotions': sorted(
                    [{'type': e['Type'], 'confidence': round(e['Confidence'], 2)} 
                     for e in face['Emotions']],
                    key=lambda x: x['confidence'],
                    reverse=True
                )[:3],  # Top 3 emotions
                'smile': face['Smile']['Value'],
                'eyeglasses': face['Eyeglasses']['Value'],
                'beard': face['Beard']['Value']
            }
            for face in faces_response['FaceDetails']
        ]
        
        # Detect text (OCR)
        try:
            text_response = rekognition.detect_text(
                Image={'S3Object': {'Bucket': bucket, 'Name': key}}
            )
            analysis['text'] = [
                {
                    'text': text['DetectedText'],
                    'type': text['Type'],
                    'confidence': round(text['Confidence'], 2)
                }
                for text in text_response['TextDetections']
                if text['Type'] == 'LINE'  # Only get lines, not individual words
            ]
        except Exception as e:
            print(f"Text detection failed (normal for some images): {str(e)}")
        
        # Content moderation
        moderation_response = rekognition.detect_moderation_labels(
            Image={'S3Object': {'Bucket': bucket, 'Name': key}},
            MinConfidence=60
        )
        analysis['moderation_labels'] = [
            {
                'name': label['Name'],
                'parent': label.get('ParentName', ''),
                'confidence': round(label['Confidence'], 2)
            }
            for label in moderation_response['ModerationLabels']
        ]
        
        # Celebrity recognition
        try:
            celebrity_response = rekognition.recognize_celebrities(
                Image={'S3Object': {'Bucket': bucket, 'Name': key}}
            )
            analysis['celebrities'] = [
                {
                    'name': celeb['Name'],
                    'confidence': round(celeb['MatchConfidence'], 2),
                    'urls': celeb.get('Urls', [])
                }
                for celeb in celebrity_response['CelebrityFaces']
            ]
        except Exception as e:
            print(f"Celebrity detection failed: {str(e)}")
        
    except Exception as e:
        print(f"Rekognition analysis error: {str(e)}")
        raise
    
    return analysis


def has_inappropriate_content(analysis):
    """Check if image has inappropriate content"""
    # Consider inappropriate if:
    # - Any moderation label with confidence > 80%
    # - Explicit nudity
    # - Violence
    
    for label in analysis['moderation_labels']:
        if label['confidence'] > 80:
            return True
        if label['name'] in ['Explicit Nudity', 'Violence', 'Graphic Violence']:
            return True
    
    return False


def send_moderation_alert(bucket, key, moderation_labels):
    """Send SNS alert for inappropriate content"""
    if not ALERT_TOPIC_ARN:
        print("No alert topic configured")
        return
    
    try:
        message = f"""
⚠️ CONTENT MODERATION ALERT

Image: s3://{bucket}/{key}
Detected Issues:
"""
        for label in moderation_labels:
            message += f"\n- {label['name']}: {label['confidence']}% confidence"
        
        sns.publish(
            TopicArn=ALERT_TOPIC_ARN,
            Subject='🚨 Inappropriate Content Detected',
            Message=message
        )
        
        print(f"✓ Moderation alert sent for {key}")
        
    except Exception as e:
        print(f"Failed to send alert: {str(e)}")


def save_metadata(image_id, bucket, key, analysis):
    """Save image metadata to DynamoDB"""
    try:
        table = dynamodb.Table(METADATA_TABLE)
        
        # Extract top labels for quick search
        top_labels = [label['name'].lower() for label in analysis['labels'][:10]]
        
        # Count faces
        face_count = len(analysis['faces'])
        
        # Check if has text
        has_text = len(analysis['text']) > 0
        
        # Check if has celebrities
        has_celebrities = len(analysis['celebrities']) > 0
        
        # Build searchable tags
        tags = set(top_labels)
        
        # Add demographic tags
        if face_count > 0:
            tags.add('has_faces')
            tags.add(f'{face_count}_faces')
            
            # Add emotion tags
            for face in analysis['faces']:
                if face['emotions']:
                    tags.add(face['emotions'][0]['type'].lower())
        
        if has_text:
            tags.add('has_text')
        
        if has_celebrities:
            tags.add('has_celebrities')
        
        # Add moderation tags
        if analysis['moderation_labels']:
            tags.add('flagged')
            for label in analysis['moderation_labels']:
                tags.add(f"mod_{label['name'].lower().replace(' ', '_')}")
        
        # Create item
        item = {
            'image_id': image_id,
            'bucket': bucket,
            'key': key,
            'upload_date': datetime.utcnow().isoformat(),
            'file_size': get_file_size(bucket, key),
            'labels': analysis['labels'],
            'faces': analysis['faces'],
            'face_count': face_count,
            'text': analysis['text'],
            'has_text': has_text,
            'moderation_labels': analysis['moderation_labels'],
            'celebrities': analysis['celebrities'],
            'has_celebrities': has_celebrities,
            'tags': list(tags),  # Searchable tags
            'processed_at': datetime.utcnow().isoformat()
        }
        
        table.put_item(Item=item)
        
        print(f"✓ Metadata saved: {image_id}")
        print(f"  Labels: {', '.join(top_labels[:5])}")
        print(f"  Faces: {face_count}")
        print(f"  Text: {has_text}")
        
    except Exception as e:
        print(f"Failed to save metadata: {str(e)}")
        raise


def get_file_size(bucket, key):
    """Get file size from S3"""
    try:
        response = s3.head_object(Bucket=bucket, Key=key)
        return response['ContentLength']
    except:
        return 0