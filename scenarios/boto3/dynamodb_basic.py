import boto3
import random
import string

def generate_suffix():
    """Generate random suffix for unique naming"""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))

def deploy(region='eu-central-1'):
    dynamodb = boto3.client('dynamodb', region_name=region)
    
    table_name = f"dynamodb-table-basic-mk-{generate_suffix()}"
    
    # Create table
    dynamodb.create_table(
        TableName=table_name,
        KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'S'}],
        BillingMode='PROVISIONED',
        ProvisionedThroughput={'ReadCapacityUnits': 1, 'WriteCapacityUnits': 1}
    )
    
    # Wait for table to be active
    waiter = dynamodb.get_waiter('table_exists')
    waiter.wait(TableName=table_name)
    
    return {
        'table_name': table_name,
        'table_arn': f"arn:aws:dynamodb:{region}:ACCOUNT:table/{table_name}"
    }


def destroy(outputs):
    """Clean up S3 bucket"""
    dynamodb = boto3.client('dynamodb')
    
    try:
        dynamodb.delete_table(TableName=outputs['table_name'])
        return True
    except Exception as e:
        print(f"Failed to delete bucket: {e}")
        return False