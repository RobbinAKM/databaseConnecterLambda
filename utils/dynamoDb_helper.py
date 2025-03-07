import boto3
import uuid
import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment Configuration
DYNAMODB_REGION = os.getenv("AWS_REGION", "us-east-1")
DYNAMODB_TABLE_NAME = os.getenv("DYNAMODB_TABLE_NAME", "SchemaTable")
DYNAMODB_LOCAL_ENDPOINT = os.getenv("DYNAMODB_LOCAL_ENDPOINT","http://localhost:8000")  # Local DynamoDB endpoint (for testing only)

def get_dynamodb_resource(region: str = DYNAMODB_REGION, endpoint_url: Optional[str] = None):
    """
    Return a DynamoDB resource. It will use DynamoDB Local if endpoint URL is provided.
    For production, `endpoint_url` should be None or not specified.

    Args:
        region (str): AWS region (default: us-east-1).
        endpoint_url (str): Optional, DynamoDB Local endpoint for local testing.

    Returns:
        boto3.resource: DynamoDB resource.
    """
    # If running locally, use local DynamoDB endpoint; else, connect to AWS DynamoDB
    if endpoint_url:
        logger.info(f"Connecting to DynamoDB Local at {endpoint_url}")
    else:
        logger.info(f"Connecting to AWS DynamoDB in region {region}")
    
    return boto3.resource("dynamodb", region_name=region, endpoint_url=endpoint_url)

def create_table_if_not_exists(dynamodb, table_name: str):
    """Create the DynamoDB table if it does not exist."""
    try:
        # Check if the table exists
        existing_table = dynamodb.Table(table_name)
        existing_table.load()  # This will raise an exception if the table doesn't exist
        logger.info(f"Table '{table_name}' already exists.")
    except dynamodb.meta.client.exceptions.ResourceNotFoundException:
        # Table does not exist, so create it
        logger.info(f"Table '{table_name}' does not exist. Creating it now...")
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': 'databaseInfo',
                    'KeyType': 'HASH'  
                },
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'databaseInfo',
                    'AttributeType': 'S'
                },
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        # Wait for the table to be created
        table.meta.client.get_waiter('table_exists').wait(TableName=table_name)
        logger.info(f"Table '{table_name}' created successfully.")

def store_schema_in_dynamodb(db_schema: Dict[str, Any], dynamodb=None) -> Optional[str]:
    """
    Store extracted database schema in DynamoDB. If the schemaId already exists, return the existing item.

    Args:
        db_schema (Dict[str, Any]): The database schema to store.
        dynamodb: (Optional) Injected DynamoDB resource for testing.

    Returns:
        Optional[str]: Schema ID if successful, None if failed.
    """
    dynamodb = dynamodb or get_dynamodb_resource(endpoint_url=DYNAMODB_LOCAL_ENDPOINT)
    table = dynamodb.Table(DYNAMODB_TABLE_NAME)

    # Ensure the table exists or create it
    create_table_if_not_exists(dynamodb, DYNAMODB_TABLE_NAME)

    schema_id = "test_1"  # This should come from FE or be dynamically generated
    # Check if the schemaId already exists
    try:
        response = table.get_item(Key={"schemaId": schema_id})
        
        if "Item" in response:
            logger.info(f"Schema with schemaId '{schema_id}' already exists. Returning the existing item.")
            existing_item = response["Item"]
 
            return {
                "schemaId": existing_item["schemaId"],
                "timestamp": existing_item["timestamp"],
                "dbSchema": existing_item["dbSchema"]
            }
        
    except ClientError as e:
        logger.error(f"Error checking for existing schema: {str(e)}")
        return None

    # If schemaId doesn't exist, create a new item
    item = {
        "schemaId": schema_id,  
        "timestamp": datetime.utcnow().isoformat(),
        "dbSchema": db_schema,
    }

    try:
        response = table.put_item(Item=item)
        logger.info(f"Database schema successfully stored in DynamoDB (ID: {schema_id})")
        logger.info(f"DynamoDB response: {response}")
        return {
            "schemaId": schema_id,
            "timestamp": item["timestamp"],
            "dbSchema": db_schema
        }
    except ClientError as e:
        logger.error(f"Error storing schema in DynamoDB: {str(e)}")
        return None
