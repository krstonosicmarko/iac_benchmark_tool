"""
EC2 Complex Scaling Scenario - Boto3 Implementation
Simple complexity: Basic EC2 + dedicated security group
Change INSTANCE_COUNT constant for different scales:
- Complex-Single: INSTANCE_COUNT = 1
- Complex-Scale-10: INSTANCE_COUNT = 10
"""

import boto3
import uuid
import time
from botocore.exceptions import ClientError

def generate_unique_suffix():
    """Generate a unique suffix for resource names"""
    return str(uuid.uuid4())[:8]

def get_default_vpc():
    """Get the default VPC"""
    ec2_client = boto3.client('ec2', region_name='eu-central-1')
    
    try:
        response = ec2_client.describe_vpcs(Filters=[{'Name': 'is-default', 'Values': ['true']}])
        if response['Vpcs']:
            return response['Vpcs'][0]['VpcId']
        else:
            raise Exception("No default VPC found")
    except ClientError as e:
        print(f"Error finding default VPC: {e}")
        return None

def get_amazon_linux_ami():
    """Get the latest Amazon Linux 2 AMI"""
    ec2_client = boto3.client('ec2', region_name='eu-central-1')
    
    try:
        response = ec2_client.describe_images(
            Owners=['amazon'],
            Filters=[
                {'Name': 'name', 'Values': ['amzn2-ami-hvm-*-x86_64-gp2']},
                {'Name': 'state', 'Values': ['available']},
                {'Name': 'virtualization-type', 'Values': ['hvm']}
            ]
        )
        
        # Sort by creation date and get the most recent
        images = sorted(response['Images'], key=lambda x: x['CreationDate'], reverse=True)
        if images:
            return images[0]['ImageId']
        else:
            raise Exception("No Amazon Linux 2 AMI found")
            
    except ClientError as e:
        print(f"Error finding Amazon Linux AMI: {e}")
        return None

def deploy(resource_count=1):
    """Deploy multiple complex EC2 instances with Boto3"""
    ec2_client = boto3.client('ec2', region_name='eu-central-1')
    
    suffix = generate_unique_suffix()
    vpc_id = get_default_vpc()
    ami_id = get_amazon_linux_ami()
    
    if not vpc_id or not ami_id:
        print("Failed to get required AWS resources")
        return None
    
    security_group_id = None
    instance_ids = []
    
    try:
        # Create security group (complexity feature)
        print("Creating security group...")
        sg_response = ec2_client.create_security_group(
            GroupName=f'ec2-complex-sg-{suffix}',
            Description='Security group for EC2 complex benchmarking',
            VpcId=vpc_id,
            TagSpecifications=[
                {
                    'ResourceType': 'security-group',
                    'Tags': [
                        {'Key': 'Name', 'Value': f'ec2-complex-sg-{suffix}'},
                        {'Key': 'Environment', 'Value': 'test'},
                        {'Key': 'Purpose', 'Value': 'benchmarking'}
                    ]
                }
            ]
        )
        
        security_group_id = sg_response['GroupId']
        print(f"✅ Security group created: {security_group_id}")
        
        # Add SSH access rule to security group
        ec2_client.authorize_security_group_ingress(
            GroupId=security_group_id,
            IpPermissions=[
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 22,
                    'ToPort': 22,
                    'IpRanges': [{'CidrIp': '10.0.0.0/8'}]  # Restrictive SSH access
                }
            ]
        )
        print(f"✅ SSH access rule added to security group")
        
        # Create multiple EC2 instances based on resource_count
        for i in range(resource_count):
            try:
                print(f"Creating instance {i+1} of {resource_count}...")
                
                # Launch EC2 instance with security group
                instance_response = ec2_client.run_instances(
                    ImageId=ami_id,
                    MinCount=1,
                    MaxCount=1,
                    InstanceType='t3.micro',
                    SecurityGroupIds=[security_group_id],
                    TagSpecifications=[
                        {
                            'ResourceType': 'instance',
                            'Tags': [
                                {'Key': 'Name', 'Value': f'test-complex-instance-{i}-{suffix}'},
                                {'Key': 'Environment', 'Value': 'test'},
                                {'Key': 'Purpose', 'Value': 'benchmarking'},
                                {'Key': 'Index', 'Value': str(i)}
                            ]
                        }
                    ]
                )
                
                instance_id = instance_response['Instances'][0]['InstanceId']
                instance_ids.append(instance_id)
                print(f"✅ Instance {i+1} created: {instance_id}")
                
            except ClientError as e:
                error_code = e.response['Error']['Code']
                print(f"❌ Error creating instance {i+1}: {error_code} - {e}")
                
                # If we hit vCPU limits or other capacity issues, cleanup and fail
                if error_code in ['VcpuLimitExceeded', 'InsufficientInstanceCapacity', 'InstanceLimitExceeded']:
                    print(f"Hit AWS limits after creating {len(instance_ids)} instances")
                    
                    # Cleanup instances
                    if instance_ids:
                        print(f"Cleaning up {len(instance_ids)} instances...")
                        try:
                            ec2_client.terminate_instances(InstanceIds=instance_ids)
                            print("✅ Instance cleanup initiated")
                        except Exception as cleanup_error:
                            print(f"❌ Error cleaning up instances: {cleanup_error}")
                    
                    # Cleanup security group
                    if security_group_id:
                        print("Waiting for instances to terminate before deleting security group...")
                        time.sleep(10)  # Give instances time to start terminating
                        try:
                            ec2_client.delete_security_group(GroupId=security_group_id)
                            print("✅ Security group cleanup initiated")
                        except Exception as sg_cleanup_error:
                            print(f"❌ Error cleaning up security group: {sg_cleanup_error}")
                            print(f"⚠️ MANUAL CLEANUP REQUIRED for security group: {security_group_id}")
                    
                    return None
                else:
                    # For other errors, still cleanup
                    print(f"Unexpected error: {e}")
                    
                    # Cleanup instances
                    if instance_ids:
                        try:
                            ec2_client.terminate_instances(InstanceIds=instance_ids)
                        except Exception as cleanup_error:
                            print(f"❌ Error cleaning up instances: {cleanup_error}")
                    
                    # Cleanup security group
                    if security_group_id:
                        time.sleep(10)
                        try:
                            ec2_client.delete_security_group(GroupId=security_group_id)
                        except Exception as sg_cleanup_error:
                            print(f"❌ Error cleaning up security group: {sg_cleanup_error}")
                    
                    return None
        
        if not instance_ids:
            print("No instances were created")
            # Still need to cleanup security group
            if security_group_id:
                try:
                    ec2_client.delete_security_group(GroupId=security_group_id)
                except Exception as sg_cleanup_error:
                    print(f"❌ Error cleaning up unused security group: {sg_cleanup_error}")
            return None
            
        print(f"All {len(instance_ids)} instances created successfully, waiting for running state...")
        
        # Wait for all instances to be running to get public IPs
        waiter = ec2_client.get_waiter('instance_running')
        waiter.wait(InstanceIds=instance_ids)
        
        # Get public IPs for all instances
        instance_public_ips = []
        instances_response = ec2_client.describe_instances(InstanceIds=instance_ids)
        for reservation in instances_response['Reservations']:
            for instance in reservation['Instances']:
                public_ip = instance.get('PublicIpAddress', '')
                instance_public_ips.append(public_ip)
        
        print(f"✅ All instances running with public IPs")
        
        return {
            "instance_ids": instance_ids,
            "instance_count": len(instance_ids),
            "instance_public_ips": instance_public_ips,
            "security_group_id": security_group_id,
            "features_enabled": {
                "security_group": "Custom SSH-only security group",
                "instance_type": "t3.micro"
            }
        }
        
    except Exception as e:
        print(f"Unexpected error in deploy(): {e}")
        
        # Emergency cleanup
        if instance_ids:
            print(f"Emergency cleanup of {len(instance_ids)} instances...")
            try:
                ec2_client.terminate_instances(InstanceIds=instance_ids)
            except Exception as cleanup_error:
                print(f"❌ Emergency instance cleanup failed: {cleanup_error}")
                print(f"⚠️ MANUAL CLEANUP REQUIRED for instances: {instance_ids}")
        
        if security_group_id:
            print("Emergency cleanup of security group...")
            time.sleep(10)
            try:
                ec2_client.delete_security_group(GroupId=security_group_id)
            except Exception as sg_cleanup_error:
                print(f"❌ Emergency security group cleanup failed: {sg_cleanup_error}")
                print(f"⚠️ MANUAL CLEANUP REQUIRED for security group: {security_group_id}")
        
        return None

def destroy(outputs, verbose):
    """Clean up multiple EC2 complex resources"""
    if not outputs:
        return False
    
    if verbose:
        print(f"Terminated {len(instance_ids)} instances")
        
    ec2_client = boto3.client('ec2', region_name='eu-central-1')
    
    try:
        instance_ids = outputs.get('instance_ids', [])
        security_group_id = outputs.get('security_group_id')
        
        # Terminate all EC2 instances first
        if instance_ids:
            ec2_client.terminate_instances(InstanceIds=instance_ids)
            
            # Wait for all instances to be terminated
            termination_waiter = ec2_client.get_waiter('instance_terminated')
            termination_waiter.wait(InstanceIds=instance_ids)
            print(f"Terminated {len(instance_ids)} instances")
        
        # Delete security group after instances are terminated
        if security_group_id:
            # Small delay to ensure instances are fully terminated
            time.sleep(10)
            try:
                ec2_client.delete_security_group(GroupId=security_group_id)
                print(f"Deleted security group: {security_group_id}")
            except ClientError as e:
                print(f"Warning: Error deleting security group {security_group_id}: {e}")
        
        return True
        
    except ClientError as e:
        print(f"Error cleaning up EC2 complex resources: {e}")
        return False