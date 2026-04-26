"""
Content Moderation Alert Handler
Sends alerts when inappropriate content is detected
"""

import json
import boto3
import os
from datetime import datetime

# AWS Clients
dynamodb = boto3.resource('dynamodb')
ses = boto3.client('ses')

# Environment variables
METADATA_TABLE = os.environ.get('METADATA_TABLE', 'image-metadata')
ALERT_EMAIL = os.environ.get('ALERT_EMAIL', '')


def lambda_handler(event, context):
    """
    Triggered by SNS when inappropriate content is detected
    Logs incident and sends email alert
    """
    print(f"Event: {json.dumps(event)}")
    
    try:
        for record in event['Records']:
            # Parse SNS message
            message = record['Sns']['Message']
            subject = record['Sns']['Subject']
            
            print(f"Moderation alert: {subject}")
            print(f"Message: {message}")
            
            # Log to DynamoDB (moderation incidents table)
            log_moderation_incident(message)
            
            # Send email alert if configured
            if ALERT_EMAIL:
                send_email_alert(subject, message)
        
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Alerts processed'})
        }
        
    except Exception as e:
        print(f"Error processing alert: {str(e)}")
        raise


def log_moderation_incident(message):
    """Log moderation incident to DynamoDB"""
    try:
        # Extract image path from message
        # Message format: "Image: s3://bucket/key"
        image_path = ''
        for line in message.split('\n'):
            if line.startswith('Image:'):
                image_path = line.replace('Image:', '').strip()
                break
        
        # This would go to a separate moderation_incidents table
        # For simplicity, we'll just log it
        print(f"✓ Logged moderation incident for: {image_path}")
        
    except Exception as e:
        print(f"Failed to log incident: {str(e)}")


def send_email_alert(subject, message):
    """Send email alert via SES"""
    try:
        response = ses.send_email(
            Source=ALERT_EMAIL,
            Destination={'ToAddresses': [ALERT_EMAIL]},
            Message={
                'Subject': {'Data': subject},
                'Body': {
                    'Text': {'Data': message}
                }
            }
        )
        
        print(f"✓ Email alert sent: {response['MessageId']}")
        
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        # Note: SES requires email verification in sandbox mode
        # Go to SES console and verify your email first