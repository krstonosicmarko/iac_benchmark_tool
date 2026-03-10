import boto3
import json
import random
import string

def generate_suffix():
    """Generate random suffix for unique naming"""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))


def deploy(region='eu-central-1'):
    iam = boto3.client('iam', region_name=region)
    
    role_name = f"benchmark-test-role-{generate_suffix()}"
    
    # Trust policy (same as your Terraform)
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "ec2.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }
    
    # Create role
    response = iam.create_role(
        RoleName=role_name,
        AssumeRolePolicyDocument=json.dumps(trust_policy)
    )
    
    role_arn = response['Role']['Arn']
    
    return {
        'role_name': role_name,
        'role_arn': role_arn
    }

def destroy(outputs):
    iam = boto3.client('iam')
    try:
        iam.delete_role(RoleName=outputs['role_name'])
        return True
    except Exception as e:
        print(f"Failed to delete role: {e}")
        return False