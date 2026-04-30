"""
Image Search API
Search images by labels, faces, text, etc.
"""

import json
import boto3
import os
from boto3.dynamodb.conditions import Attr, Key
from decimal import Decimal

# AWS Clients
dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')

# Environment variables
METADATA_TABLE = os.environ.get('METADATA_TABLE', 'image-metadata')
IMAGES_BUCKET = os.environ.get('IMAGES_BUCKET', '')

# CORS Headers
CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
}


def decimal_to_float(obj):
    """
    Recursively convert Decimal to float for JSON serialization
    """
    if isinstance(obj, list):
        return [decimal_to_float(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: decimal_to_float(value) for key, value in obj.items()}
    elif isinstance(obj, Decimal):
        return float(obj)
    else:
        return obj


def lambda_handler(event, context):
    """
    Main handler - routes requests
    """
    print(f"Event: {json.dumps(event)}")
    
    http_method = event.get('httpMethod', '')
    path = event.get('path', '')
    
    if http_method == 'OPTIONS':
        return cors_response(200, {'message': 'OK'})
    
    elif http_method == 'GET' and '/search' in path:
        return handle_search(event)
    
    elif http_method == 'GET' and '/image/' in path:
        return handle_get_image(event)
    
    elif http_method == 'GET' and '/stats' in path:
        return handle_get_stats(event)
    
    else:
        return cors_response(404, {'error': 'Not found'})


def handle_search(event):
    """
    Search images by query parameters
    """
    try:
        params = event.get('queryStringParameters') or {}
        
        # Search parameters
        query = params.get('q', '').lower()  # General search
        label = params.get('label', '').lower()  # Specific label
        has_faces = params.get('faces', '').lower() == 'true'
        has_text = params.get('text', '').lower() == 'true'
        limit = int(params.get('limit', '20'))
        
        table = dynamodb.Table(METADATA_TABLE)
        
        # Build filter expression
        filter_expr = None
        
        if query:
            # Search in tags
            filter_expr = Attr('tags').contains(query)
        
        if label:
            if filter_expr:
                filter_expr = filter_expr & Attr('tags').contains(label)
            else:
                filter_expr = Attr('tags').contains(label)
        
        if has_faces:
            if filter_expr:
                filter_expr = filter_expr & Attr('face_count').gt(0)
            else:
                filter_expr = Attr('face_count').gt(0)
        
        if has_text:
            if filter_expr:
                filter_expr = filter_expr & Attr('has_text').eq(True)
            else:
                filter_expr = Attr('has_text').eq(True)
        
        # Scan table with filter
        if filter_expr:
            response = table.scan(
                FilterExpression=filter_expr,
                Limit=limit
            )
        else:
            response = table.scan(Limit=limit)
        
        items = response.get('Items', [])
        
        # Generate signed URLs for images
        results = []
        for item in items:
            # Convert Decimal to float for JSON
            item = decimal_to_float(item)
            
            results.append({
                'image_id': item['image_id'],
                'url': generate_signed_url(item['bucket'], item['key']),
                'upload_date': item['upload_date'],
                'labels': [l['name'] for l in item.get('labels', [])[:5]],
                'face_count': item.get('face_count', 0),
                'has_text': item.get('has_text', False),
                'file_size': item.get('file_size', 0)
            })
        
        return cors_response(200, {
            'results': results,
            'count': len(results),
            'query': {
                'q': query,
                'label': label,
                'has_faces': has_faces,
                'has_text': has_text
            }
        })
        
    except Exception as e:
        print(f"Search error: {str(e)}")
        return cors_response(500, {'error': 'Internal server error'})


def handle_get_image(event):
    """
    Get full image metadata by ID
    """
    try:
        # Extract image_id from path
        path = event.get('path', '')
        image_id = path.split('/')[-1]
        
        table = dynamodb.Table(METADATA_TABLE)
        
        response = table.get_item(Key={'image_id': image_id})
        
        if 'Item' not in response:
            return cors_response(404, {'error': 'Image not found'})
        
        item = response['Item']
        
        # Convert Decimal to float for JSON
        item = decimal_to_float(item)
        
        # Generate signed URL
        signed_url = generate_signed_url(item['bucket'], item['key'])
        
        # Format response
        image_data = {
            'image_id': item['image_id'],
            'url': signed_url,
            'upload_date': item['upload_date'],
            'file_size': item.get('file_size', 0),
            'labels': item.get('labels', []),
            'faces': item.get('faces', []),
            'text': item.get('text', []),
            'celebrities': item.get('celebrities', []),
            'moderation_labels': item.get('moderation_labels', []),
            'tags': item.get('tags', [])
        }
        
        return cors_response(200, image_data)
        
    except Exception as e:
        print(f"Get image error: {str(e)}")
        return cors_response(500, {'error': 'Internal server error'})


def handle_get_stats(event):
    """
    Get overall statistics
    """
    try:
        table = dynamodb.Table(METADATA_TABLE)
        
        # Scan all items (for small datasets)
        response = table.scan()
        items = response.get('Items', [])
        
        # Convert Decimal to float
        items = [decimal_to_float(item) for item in items]
        
        # Calculate stats
        total_images = len(items)
        total_faces = sum(item.get('face_count', 0) for item in items)
        images_with_text = sum(1 for item in items if item.get('has_text'))
        images_with_celebrities = sum(1 for item in items if item.get('has_celebrities'))
        flagged_images = sum(1 for item in items if item.get('moderation_labels'))
        
        # Top labels
        label_counts = {}
        for item in items:
            for label in item.get('labels', [])[:5]:
                name = label['name']
                label_counts[name] = label_counts.get(name, 0) + 1
        
        top_labels = sorted(
            label_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        stats = {
            'total_images': total_images,
            'total_faces_detected': total_faces,
            'images_with_text': images_with_text,
            'images_with_celebrities': images_with_celebrities,
            'flagged_images': flagged_images,
            'top_labels': [{'label': l[0], 'count': l[1]} for l in top_labels]
        }
        
        return cors_response(200, stats)
        
    except Exception as e:
        print(f"Stats error: {str(e)}")
        return cors_response(500, {'error': 'Internal server error'})


def generate_signed_url(bucket, key, expiration=3600):
    """Generate pre-signed URL for S3 object"""
    try:
        url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket, 'Key': key},
            ExpiresIn=expiration
        )
        return url
    except Exception as e:
        print(f"Error generating signed URL: {str(e)}")
        return ''


def cors_response(status_code, body):
    """Helper to return CORS-enabled response"""
    return {
        'statusCode': status_code,
        'headers': CORS_HEADERS,
        'body': json.dumps(body)
    }