"""
EC2 Basic Scaling Scenario - Boto3 Implementation
Change INSTANCE_COUNT constant for different scales:
- Single: INSTANCE_COUNT = 1
- Scale-10: INSTANCE_COUNT = 10  
- Scale-25: INSTANCE_COUNT = 25
"""

import boto3
import uuid
from botocore.exceptions import ClientError

def generate_unique_suffix():
    """Generate a unique suffix for resource names"""
    return str(uuid.uuid4())[:8]

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
    """Deploy multiple basic EC2 instances with Boto3"""
    ec2_client = boto3.client('ec2', region_name='eu-central-1')
    
    suffix = generate_unique_suffix()
    ami_id = get_amazon_linux_ami()
    
    if not ami_id:
        print("Failed to get Amazon Linux AMI")
        return None
    
    instance_ids = []
    
    try:
        # Create multiple EC2 instances based on resource_count
        for i in range(resource_count):
            try:
                print(f"Creating instance {i+1} of {resource_count}...")
                
                # Launch EC2 instance
                instance_response = ec2_client.run_instances(
                    ImageId=ami_id,
                    MinCount=1,
                    MaxCount=1,
                    InstanceType='t3.micro',
                    TagSpecifications=[
                        {
                            'ResourceType': 'instance',
                            'Tags': [
                                {'Key': 'Name', 'Value': f'test-basic-instance-{i}-{suffix}'},
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
                    if instance_ids:
                        print(f"Cleaning up {len(instance_ids)} successfully created instances...")
                        try:
                            ec2_client.terminate_instances(InstanceIds=instance_ids)
                            print("✅ Cleanup initiated for partial deployment")
                        except Exception as cleanup_error:
                            print(f"❌ Error during cleanup: {cleanup_error}")
                            print(f"⚠️ MANUAL CLEANUP REQUIRED for instances: {instance_ids}")
                    return None
                else:
                    # For other errors, still cleanup but might be worth retrying
                    print(f"Unexpected error: {e}")
                    if instance_ids:
                        print(f"Cleaning up {len(instance_ids)} instances due to error...")
                        try:
                            ec2_client.terminate_instances(InstanceIds=instance_ids)
                        except Exception as cleanup_error:
                            print(f"❌ Error during cleanup: {cleanup_error}")
                    return None
        
        if not instance_ids:
            print("No instances were created")
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
            "instance_public_ips": instance_public_ips
        }
        
    except Exception as e:
        print(f"Unexpected error in deploy(): {e}")
        # Emergency cleanup
        if instance_ids:
            print(f"Emergency cleanup of {len(instance_ids)} instances...")
            try:
                ec2_client.terminate_instances(InstanceIds=instance_ids)
            except Exception as cleanup_error:
                print(f"❌ Emergency cleanup failed: {cleanup_error}")
                print(f"⚠️ MANUAL CLEANUP REQUIRED for instances: {instance_ids}")
        return None
    
def destroy(outputs, verbose):
    """Clean up multiple EC2 basic resources"""
    if not outputs:
        return False
    
    if verbose:
        print(f"Terminated {len(instance_ids)} instances")
        
    ec2_client = boto3.client('ec2', region_name='eu-central-1')
    instance_ids = outputs.get('instance_ids', [])
    
    if not instance_ids:
        return False
    
    try:
        # Terminate all EC2 instances
        ec2_client.terminate_instances(InstanceIds=instance_ids)
        
        # Wait for all instances to be terminated
        waiter = ec2_client.get_waiter('instance_terminated')
        waiter.wait(InstanceIds=instance_ids)
        
        print(f"Terminated {len(instance_ids)} instances")
        return True
        
    except ClientError as e:
        print(f"Error cleaning up EC2 basic resources: {e}")
        return False