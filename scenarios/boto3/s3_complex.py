"""
S3 Complex Scaling Scenario - Boto3 Implementation
Simple complexity: Basic bucket + encryption + versioning
Change BUCKET_COUNT constant for different scales:
- Complex-Single: BUCKET_COUNT = 1
- Complex-Scale-10: BUCKET_COUNT = 10
"""

import boto3
import uuid
from botocore.exceptions import ClientError

def generate_unique_suffix():
    """Generate a unique suffix for bucket names"""
    return str(uuid.uuid4())[:8]

def deploy(resource_count=1):
    """Deploy multiple complex S3 buckets with Boto3"""
    s3_client = boto3.client('s3', region_name='eu-central-1')
    
    suffix = generate_unique_suffix()
    region = 'eu-central-1'
    bucket_names = []
    
    try:
        # Create multiple complex S3 buckets based on resource_count
        for i in range(resource_count):
            bucket_name = f"test-complex-bucket-mk-{i}-{suffix}"
            
            # Create S3 bucket
            s3_client.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={'LocationConstraint': region}
            )
            
            # Add tags to bucket
            s3_client.put_bucket_tagging(
                Bucket=bucket_name,
                Tagging={
                    'TagSet': [
                        {'Key': 'Name', 'Value': f'test-complex-bucket-{i}'},
                        {'Key': 'Environment', 'Value': 'test'},
                        {'Key': 'Purpose', 'Value': 'benchmarking'},
                        {'Key': 'Index', 'Value': str(i)}
                    ]
                }
            )
            
            # Enable versioning (complexity feature 1)
            s3_client.put_bucket_versioning(
                Bucket=bucket_name,
                VersioningConfiguration={'Status': 'Enabled'}
            )
            
            # Configure server-side encryption (complexity feature 2)
            s3_client.put_bucket_encryption(
                Bucket=bucket_name,
                ServerSideEncryptionConfiguration={
                    'Rules': [
                        {
                            'ApplyServerSideEncryptionByDefault': {
                                'SSEAlgorithm': 'AES256'
                            }
                        }
                    ]
                }
            )
            
            bucket_names.append(bucket_name)
            
        return {
            "bucket_names": bucket_names,
            "bucket_count": len(bucket_names),
            "bucket_region": region,
            "features_enabled": {
                "versioning": "Enabled",
                "encryption": "AES256"
            }
        }
        
    except ClientError as e:
        print(f"Error creating S3 complex resources: {e}")
        return None

def destroy(outputs, verbose):
    """Clean up multiple S3 complex resources"""
    if not outputs:
        return False
        
    s3_client = boto3.client('s3', region_name='eu-central-1')
    bucket_names = outputs.get('bucket_names', [])
    
    if not bucket_names:
        return False
    
    try:
        # Delete all complex buckets
        for bucket_name in bucket_names:
            try:
                # For versioned buckets, need to delete all versions first
                try:
                    # Get all object versions and delete markers
                    paginator = s3_client.get_paginator('list_object_versions')
                    page_iterator = paginator.paginate(Bucket=bucket_name)
                    
                    for page in page_iterator:
                        # Delete object versions
                        if 'Versions' in page:
                            objects_to_delete = [
                                {'Key': obj['Key'], 'VersionId': obj['VersionId']} 
                                for obj in page['Versions']
                            ]
                            if objects_to_delete:
                                s3_client.delete_objects(
                                    Bucket=bucket_name,
                                    Delete={'Objects': objects_to_delete}
                                )
                        
                        # Delete delete markers
                        if 'DeleteMarkers' in page:
                            delete_markers_to_delete = [
                                {'Key': obj['Key'], 'VersionId': obj['VersionId']} 
                                for obj in page['DeleteMarkers']
                            ]
                            if delete_markers_to_delete:
                                s3_client.delete_objects(
                                    Bucket=bucket_name,
                                    Delete={'Objects': delete_markers_to_delete}
                                )
                except ClientError:
                    # If no versions exist, continue with bucket deletion
                    pass
                
                # Delete the bucket
                s3_client.delete_bucket(Bucket=bucket_name)
                if verbose:
                    print(f"Deleted complex bucket: {bucket_name}")
                
            except ClientError as e:
                print(f"Error deleting complex bucket {bucket_name}: {e}")
                return False
        
        return True
        
    except ClientError as e:
        print(f"Error cleaning up S3 complex resources: {e}")
        return False