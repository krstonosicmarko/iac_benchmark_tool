import boto3
import random
import string

def generate_suffix():
    """Generate random suffix for unique naming"""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))

def deploy(region='eu-central-1'):
    ec2 = boto3.client('ec2', region_name=region)
    
    # Create VPC
    vpc_response = ec2.create_vpc(CidrBlock='10.0.0.0/16')
    vpc_id = vpc_response['Vpc']['VpcId']
    
    # Enable DNS hostnames
    ec2.modify_vpc_attribute(VpcId=vpc_id, EnableDnsHostnames={'Value': True})
    
    # Create subnet
    subnet_response = ec2.create_subnet(
        VpcId=vpc_id,
        CidrBlock='10.0.1.0/24',
        AvailabilityZone=f'{region}a'
    )
    subnet_id = subnet_response['Subnet']['SubnetId']
    
    # Tag resources
    ec2.create_tags(
        Resources=[vpc_id],
        Tags=[{'Key': 'Name', 'Value': 'benchmark-vpc'}]
    )
    ec2.create_tags(
        Resources=[subnet_id],
        Tags=[{'Key': 'Name', 'Value': 'benchmark-subnet'}]
    )
    
    return {
        'vpc_id': vpc_id,
        'vpc_cidr': '10.0.0.0/16',
        'subnet_id': subnet_id,
        'subnet_cidr': '10.0.1.0/24'
    }

def destroy(outputs):
    ec2 = boto3.client('ec2')
    try:
        # Delete subnet first
        ec2.delete_subnet(SubnetId=outputs['subnet_id'])
        # Then delete VPC
        ec2.delete_vpc(VpcId=outputs['vpc_id'])
        return True
    except Exception as e:
        print(f"Failed to delete VPC resources: {e}")
        return False