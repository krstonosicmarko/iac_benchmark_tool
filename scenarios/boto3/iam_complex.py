"""
IAM Complex Scenario - Boto3 Implementation
Role + 1 custom policy attachment (scaled down from user/group complexity)
"""

import boto3
import uuid
import json
import time
from botocore.exceptions import ClientError

def generate_unique_name():
    """Generate a unique resource name suffix"""
    return str(uuid.uuid4())[:8]

def get_assume_role_policy():
    """Get the trust policy document for EC2 service"""
    return {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "ec2.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }

def get_s3_readonly_policy():
    """Get the custom S3 read-only policy document"""
    return {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "s3:GetObject",
                    "s3:ListBucket"
                ],
                "Resource": [
                    "arn:aws:s3:::*",
                    "arn:aws:s3:::*/*"
                ]
            }
        ]
    }

def deploy():
    """Deploy IAM complex resources with Boto3"""
    iam_client = boto3.client('iam', region_name='eu-central-1')
    
    resource_suffix = generate_unique_name()
    role_name = f'iam-complex-role-{resource_suffix}'
    policy_name = f'iam-complex-s3-readonly-{resource_suffix}'
    instance_profile_name = f'iam-complex-profile-{resource_suffix}'
    
    try:
        # Create IAM Role
        role_response = iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(get_assume_role_policy()),
            Description='IAM role for complex benchmarking scenario',
            Tags=[
                {'Key': 'Name', 'Value': role_name},
                {'Key': 'Environment', 'Value': 'test'},
                {'Key': 'Purpose', 'Value': 'benchmarking'}
            ]
        )
        
        role_arn = role_response['Role']['Arn']
        
        # Create custom IAM Policy
        policy_response = iam_client.create_policy(
            PolicyName=policy_name,
            Path='/',
            PolicyDocument=json.dumps(get_s3_readonly_policy()),
            Description='Custom S3 read-only policy for benchmarking',
            Tags=[
                {'Key': 'Name', 'Value': policy_name},
                {'Key': 'Environment', 'Value': 'test'},
                {'Key': 'Purpose', 'Value': 'benchmarking'}
            ]
        )
        
        policy_arn = policy_response['Policy']['Arn']
        
        # Wait for role to be available (IAM eventual consistency)
        time.sleep(2)
        
        # Attach custom policy to role
        iam_client.attach_role_policy(
            RoleName=role_name,
            PolicyArn=policy_arn
        )
        
        # Create instance profile
        instance_profile_response = iam_client.create_instance_profile(
            InstanceProfileName=instance_profile_name,
            Tags=[
                {'Key': 'Name', 'Value': instance_profile_name},
                {'Key': 'Environment', 'Value': 'test'},
                {'Key': 'Purpose', 'Value': 'benchmarking'}
            ]
        )
        
        # Add role to instance profile
        iam_client.add_role_to_instance_profile(
            InstanceProfileName=instance_profile_name,
            RoleName=role_name
        )
        
        # Wait for eventual consistency
        time.sleep(2)
        
        return {
            "role_name": role_name,
            "role_arn": role_arn,
            "policy_name": policy_name,
            "policy_arn": policy_arn,
            "instance_profile_name": instance_profile_name
        }
        
    except ClientError as e:
        print(f"Error creating IAM complex resources: {e}")
        return None

def destroy(outputs):
    """Clean up IAM complex resources"""
    if not outputs:
        return False
        
    iam_client = boto3.client('iam', region_name='eu-central-1')
    
    try:
        role_name = outputs.get('role_name')
        policy_arn = outputs.get('policy_arn')
        instance_profile_name = outputs.get('instance_profile_name')
        
        # Remove role from instance profile
        if instance_profile_name and role_name:
            try:
                iam_client.remove_role_from_instance_profile(
                    InstanceProfileName=instance_profile_name,
                    RoleName=role_name
                )
            except ClientError as e:
                print(f"Warning: Error removing role from instance profile: {e}")
        
        # Delete instance profile
        if instance_profile_name:
            try:
                iam_client.delete_instance_profile(
                    InstanceProfileName=instance_profile_name
                )
            except ClientError as e:
                print(f"Warning: Error deleting instance profile: {e}")
        
        # Detach policy from role
        if role_name and policy_arn:
            try:
                iam_client.detach_role_policy(
                    RoleName=role_name,
                    PolicyArn=policy_arn
                )
            except ClientError as e:
                print(f"Warning: Error detaching policy from role: {e}")
        
        # Delete custom policy
        if policy_arn:
            try:
                iam_client.delete_policy(PolicyArn=policy_arn)
            except ClientError as e:
                print(f"Warning: Error deleting policy: {e}")
        
        # Delete role
        if role_name:
            try:
                iam_client.delete_role(RoleName=role_name)
            except ClientError as e:
                print(f"Warning: Error deleting role: {e}")
        
        return True
        
    except ClientError as e:
        print(f"Error cleaning up IAM complex resources: {e}")
        return False