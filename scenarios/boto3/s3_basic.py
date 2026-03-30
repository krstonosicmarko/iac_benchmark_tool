"""
S3 Basic Scaling Scenario - Boto3 Implementation
Change BUCKET_COUNT constant for different scales:
- Single: BUCKET_COUNT = 1
- Scale-10: BUCKET_COUNT = 10  
- Scale-25: BUCKET_COUNT = 25
"""

import boto3
import uuid
from botocore.exceptions import ClientError

def generate_unique_suffix():
    """Generate a unique suffix for bucket names"""
    return str(uuid.uuid4())[:8]

def deploy(resource_count=1):
    """Deploy multiple basic S3 buckets with Boto3"""
    s3_client = boto3.client('s3', region_name='eu-central-1')
    
    suffix = generate_unique_suffix()
    region = 'eu-central-1'
    bucket_names = []
    
    try:
        # Create multiple S3 buckets based on resource_count
        for i in range(resource_count):
            bucket_name = f"test-basic-bucket-mk-{i}-{suffix}"
            
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
                        {'Key': 'Name', 'Value': f'test-basic-bucket-{i}'},
                        {'Key': 'Environment', 'Value': 'test'},
                        {'Key': 'Purpose', 'Value': 'benchmarking'},
                        {'Key': 'Index', 'Value': str(i)}
                    ]
                }
            )
            
            bucket_names.append(bucket_name)
            
        return {
            "bucket_names": bucket_names,
            "bucket_count": len(bucket_names),
            "bucket_region": region
        }
        
    except ClientError as e:
        print(f"Error creating S3 basic resources: {e}")
        return None

def destroy(outputs, verbose):
    """Clean up multiple S3 basic resources"""
    if not outputs:
        return False
        
    s3_client = boto3.client('s3', region_name='eu-central-1')
    bucket_names = outputs.get('bucket_names', [])
    
    if not bucket_names:
        return False
    
    try:
        # Delete all buckets
        for bucket_name in bucket_names:
            try:
                # Delete the bucket
                s3_client.delete_bucket(Bucket=bucket_name)
                if verbose:
                    print(f"Deleted bucket: {bucket_name}")
            except ClientError as e:
                print(f"Error deleting bucket {bucket_name}: {e}")
                return False
        
        return True
        
    except ClientError as e:
        print(f"Error cleaning up S3 basic resources: {e}")
        return False