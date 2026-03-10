"""
VPC Complex Scenario - Boto3 Implementation
VPC + 2 subnets + internet gateway (scaled down from NAT gateway and route tables)
"""

import boto3
import uuid
from botocore.exceptions import ClientError

def generate_unique_name():
    """Generate a unique resource name suffix"""
    return str(uuid.uuid4())[:8]

def get_availability_zones():
    """Get available availability zones"""
    ec2_client = boto3.client('ec2', region_name='eu-central-1')
    
    try:
        response = ec2_client.describe_availability_zones(
            Filters=[{'Name': 'state', 'Values': ['available']}]
        )
        az_names = [az['ZoneName'] for az in response['AvailabilityZones']]
        return az_names[:2]  # Return first 2 AZs
    except ClientError as e:
        print(f"Error getting availability zones: {e}")
        return ['eu-central-1a', 'eu-central-1b']  # Fallback

def deploy():
    """Deploy VPC complex resources with Boto3"""
    ec2_client = boto3.client('ec2', region_name='eu-central-1')
    
    resource_suffix = generate_unique_name()
    availability_zones = get_availability_zones()
    
    try:
        # Create VPC
        vpc_response = ec2_client.create_vpc(
            CidrBlock='10.0.0.0/16',
            TagSpecifications=[
                {
                    'ResourceType': 'vpc',
                    'Tags': [
                        {'Key': 'Name', 'Value': f'vpc-complex-{resource_suffix}'},
                        {'Key': 'Environment', 'Value': 'test'},
                        {'Key': 'Purpose', 'Value': 'benchmarking'}
                    ]
                }
            ]
        )
        
        vpc_id = vpc_response['Vpc']['VpcId']
        
        # Enable DNS support and DNS hostnames
        ec2_client.modify_vpc_attribute(
            VpcId=vpc_id,
            EnableDnsSupport={'Value': True}
        )
        
        ec2_client.modify_vpc_attribute(
            VpcId=vpc_id,
            EnableDnsHostnames={'Value': True}
        )
        
        # Create Internet Gateway
        igw_response = ec2_client.create_internet_gateway(
            TagSpecifications=[
                {
                    'ResourceType': 'internet-gateway',
                    'Tags': [
                        {'Key': 'Name', 'Value': f'igw-complex-{resource_suffix}'},
                        {'Key': 'Environment', 'Value': 'test'},
                        {'Key': 'Purpose', 'Value': 'benchmarking'}
                    ]
                }
            ]
        )
        
        igw_id = igw_response['InternetGateway']['InternetGatewayId']
        
        # Attach Internet Gateway to VPC
        ec2_client.attach_internet_gateway(
            InternetGatewayId=igw_id,
            VpcId=vpc_id
        )
        
        # Create first subnet
        subnet_1_response = ec2_client.create_subnet(
            VpcId=vpc_id,
            CidrBlock='10.0.1.0/24',
            AvailabilityZone=availability_zones[0],
            TagSpecifications=[
                {
                    'ResourceType': 'subnet',
                    'Tags': [
                        {'Key': 'Name', 'Value': f'subnet-complex-1-{resource_suffix}'},
                        {'Key': 'Environment', 'Value': 'test'},
                        {'Key': 'Purpose', 'Value': 'benchmarking'},
                        {'Key': 'Type', 'Value': 'public'}
                    ]
                }
            ]
        )
        
        subnet_1_id = subnet_1_response['Subnet']['SubnetId']
        
        # Enable auto-assign public IP for first subnet
        ec2_client.modify_subnet_attribute(
            SubnetId=subnet_1_id,
            MapPublicIpOnLaunch={'Value': True}
        )
        
        # Create second subnet
        subnet_2_response = ec2_client.create_subnet(
            VpcId=vpc_id,
            CidrBlock='10.0.2.0/24',
            AvailabilityZone=availability_zones[1],
            TagSpecifications=[
                {
                    'ResourceType': 'subnet',
                    'Tags': [
                        {'Key': 'Name', 'Value': f'subnet-complex-2-{resource_suffix}'},
                        {'Key': 'Environment', 'Value': 'test'},
                        {'Key': 'Purpose', 'Value': 'benchmarking'},
                        {'Key': 'Type', 'Value': 'public'}
                    ]
                }
            ]
        )
        
        subnet_2_id = subnet_2_response['Subnet']['SubnetId']
        
        # Enable auto-assign public IP for second subnet
        ec2_client.modify_subnet_attribute(
            SubnetId=subnet_2_id,
            MapPublicIpOnLaunch={'Value': True}
        )
        
        # Create route table
        rt_response = ec2_client.create_route_table(
            VpcId=vpc_id,
            TagSpecifications=[
                {
                    'ResourceType': 'route-table',
                    'Tags': [
                        {'Key': 'Name', 'Value': f'rt-public-complex-{resource_suffix}'},
                        {'Key': 'Environment', 'Value': 'test'},
                        {'Key': 'Purpose', 'Value': 'benchmarking'}
                    ]
                }
            ]
        )
        
        route_table_id = rt_response['RouteTable']['RouteTableId']
        
        # Add route to Internet Gateway
        ec2_client.create_route(
            RouteTableId=route_table_id,
            DestinationCidrBlock='0.0.0.0/0',
            GatewayId=igw_id
        )
        
        # Associate route table with first subnet
        ec2_client.associate_route_table(
            SubnetId=subnet_1_id,
            RouteTableId=route_table_id
        )
        
        # Associate route table with second subnet
        ec2_client.associate_route_table(
            SubnetId=subnet_2_id,
            RouteTableId=route_table_id
        )
        
        return {
            "vpc_id": vpc_id,
            "vpc_cidr": "10.0.0.0/16",
            "internet_gateway_id": igw_id,
            "subnet_1_id": subnet_1_id,
            "subnet_1_cidr": "10.0.1.0/24",
            "subnet_2_id": subnet_2_id,
            "subnet_2_cidr": "10.0.2.0/24"
        }
        
    except ClientError as e:
        print(f"Error creating VPC complex resources: {e}")
        return None

def destroy(outputs):
    """Clean up VPC complex resources"""
    if not outputs:
        return False
        
    ec2_client = boto3.client('ec2', region_name='eu-central-1')
    
    try:
        vpc_id = outputs.get('vpc_id')
        igw_id = outputs.get('internet_gateway_id')
        
        if not vpc_id:
            return False
        
        # Get all subnets in the VPC
        subnets_response = ec2_client.describe_subnets(
            Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]
        )
        
        # Delete all subnets
        for subnet in subnets_response['Subnets']:
            subnet_id = subnet['SubnetId']
            try:
                ec2_client.delete_subnet(SubnetId=subnet_id)
            except ClientError as e:
                print(f"Warning: Error deleting subnet {subnet_id}: {e}")
        
        # Get all route tables (except main) and delete them
        route_tables_response = ec2_client.describe_route_tables(
            Filters=[
                {'Name': 'vpc-id', 'Values': [vpc_id]},
                {'Name': 'association.main', 'Values': ['false']}
            ]
        )
        
        for route_table in route_tables_response['RouteTables']:
            rt_id = route_table['RouteTableId']
            try:
                ec2_client.delete_route_table(RouteTableId=rt_id)
            except ClientError as e:
                print(f"Warning: Error deleting route table {rt_id}: {e}")
        
        # Detach and delete Internet Gateway
        if igw_id:
            try:
                ec2_client.detach_internet_gateway(
                    InternetGatewayId=igw_id,
                    VpcId=vpc_id
                )
                ec2_client.delete_internet_gateway(InternetGatewayId=igw_id)
            except ClientError as e:
                print(f"Warning: Error cleaning up Internet Gateway {igw_id}: {e}")
        
        # Delete VPC
        ec2_client.delete_vpc(VpcId=vpc_id)
        
        return True
        
    except ClientError as e:
        print(f"Error cleaning up VPC complex resources: {e}")
        return False