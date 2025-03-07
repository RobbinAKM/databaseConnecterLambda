import json
import os
from sqlalchemy import create_engine, MetaData, inspect
from sqlalchemy.sql import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.engine import Engine
import logging


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_db_connection(engine: Engine) -> bool:
    """
    Tests the connection to the database by executing a simple query.

    Args:
        engine (Engine): SQLAlchemy database engine instance.

    Returns:
        bool: True if connection is successful, False otherwise.
    """
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT NOW();"))
            current_time = result.scalar()  # Fetch the first column of the first row
            logger.info(f"Connected Successfully! Current Time: {current_time}")
            return True
    except SQLAlchemyError as e:
        logger.error(f"Error connecting to the database: {e}")
        return False




def get_database_schema(engine: Engine) -> dict:
    """
    Extracts and returns the schema of a given database.

    Args:
        engine (Engine): SQLAlchemy database engine instance.

    Returns:
        dict: Database schema containing tables, columns, foreign keys, indexes, and primary keys.
    """
    try:
        metadata = MetaData()
        metadata.reflect(bind=engine)

        inspector = inspect(engine)
        schema = {"tables": inspector.get_table_names()}

        for table_name in schema["tables"]:
            table_schema = {
                "columns": [],
                "foreign_keys": [],
                "indexes": [],
                "primary_keys": []
            }

            # Get column details
            for col in inspector.get_columns(table_name):
                table_schema["columns"].append({
                    "name": col["name"],
                    "type": str(col["type"]),
                    "primary_key": col.get("primary_key", False)
                })

            # Get foreign keys
            for fk in inspector.get_foreign_keys(table_name):
                table_schema["foreign_keys"].append({
                    "column": fk["constrained_columns"],
                    "referenced_table": fk["referred_table"],
                    "referenced_columns": fk["referred_columns"]
                })

            # Get indexes
            for idx in inspector.get_indexes(table_name):
                table_schema["indexes"].append({
                    "name": idx["name"],
                    "columns": idx["column_names"],
                    "unique": idx.get("unique", False)
                })

            # Get primary keys
            table_schema["primary_keys"] = inspector.get_pk_constraint(table_name).get("constrained_columns", [])

            # Store table schema
            schema[table_name] = table_schema

        return schema

    except Exception as e:
        logger.error(f"Error fetching database schema: {e}")
        return {"error": str(e)}

