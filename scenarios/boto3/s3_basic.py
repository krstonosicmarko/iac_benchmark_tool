import boto3
import random
import string

def generate_suffix():
    """Generate random suffix for unique naming"""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))

def deploy(region='eu-north-1'):
    """Deploy S3 bucket using Boto3"""
    s3_client = boto3.client('s3', region_name=region)
    
    bucket_name = f"test-bucket-mk-{generate_suffix()}"
    
    s3_client.create_bucket(
        Bucket=bucket_name,
        CreateBucketConfiguration={'LocationConstraint': region}
    )
    
    return {
        'bucket_name': bucket_name,
        'bucket_region': region
    }

def destroy(outputs):
    """Clean up S3 bucket"""
    s3_client = boto3.client('s3')
    
    try:
        s3_client.delete_bucket(Bucket=outputs['bucket_name'])
        return True
    except Exception as e:
        print(f"Failed to delete bucket: {e}")
        return False