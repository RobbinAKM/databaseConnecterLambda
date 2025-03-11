import json
import logging
from utils.db_helper import test_db_connection, get_database_schema
from utils.dynamoDb_helper import store_schema_in_dynamodb
from sqlalchemy import create_engine


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# TODO: Use AWS SSM Parameter Store instead of hardcoded credentials
DB_USER = "admin"
DB_PASSWORD = "Kichijoji1192"
DB_HOST = "database-3.cns6y4agc4rg.ap-southeast-2.rds.amazonaws.com"
DB_PORT = "3306"
DB_NAME = "my_database"

# SQLAlchemy Database URL
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create database engine
engine = create_engine(DATABASE_URL, echo=False)  

def lambda_handler(event, context):
    """AWS Lambda handler function."""

    try:
        # Test DB connection
        is_db_connected = test_db_connection(engine)

        if is_db_connected:
            db_schema = get_database_schema(engine)
            db_info=store_schema_in_dynamodb(db_schema)  
        else:
            db_schema = None

        response_body = {
            "isDbConnected": is_db_connected,
            "dbInfo":db_info
        }

        return {"statusCode": 200, "body": json.dumps(response_body)}

    except Exception as e:
        logger.error(f"Error in lambda_handler: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal Server Error"})
        }