# Example: PostgreSQL database connection for localhost:5432
# This file demonstrates how to create a database connection for use with the readers

import psycopg2
from psycopg2 import pool
from typing import Optional

# Option 1: Simple connection (for single operations)
def create_db_connection(
    host: str = "localhost",
    port: int = 5432,
    database: str = "your_database_name",
    user: str = "your_username",
    password: str = "your_password",
) -> psycopg2.extensions.connection:
    """
    Create a PostgreSQL database connection.
    
    Args:
        host: Database host (default: localhost)
        port: Database port (default: 5432)
        database: Database name
        user: Database user
        password: Database password
    
    Returns:
        psycopg2 connection object
    """
    connection = psycopg2.connect(
        host=host,
        port=port,
        database=database,
        user=user,
        password=password,
    )
    return connection


# Option 2: Connection using connection string
def create_db_connection_from_string(
    connection_string: str,
) -> psycopg2.extensions.connection:
    """
    Create a PostgreSQL database connection from a connection string.
    
    Args:
        connection_string: PostgreSQL connection string
            Format: "host=localhost port=5432 dbname=mydb user=myuser password=mypass"
    
    Returns:
        psycopg2 connection object
    """
    connection = psycopg2.connect(connection_string)
    return connection


# Option 3: Connection pool (recommended for production)
def create_connection_pool(
    min_conn: int = 1,
    max_conn: int = 10,
    host: str = "localhost",
    port: int = 5432,
    database: str = "your_database_name",
    user: str = "your_username",
    password: str = "your_password",
) -> psycopg2.pool.ThreadedConnectionPool:
    """
    Create a connection pool for better performance.
    
    Args:
        min_conn: Minimum number of connections in the pool
        max_conn: Maximum number of connections in the pool
        host: Database host
        port: Database port
        database: Database name
        user: Database user
        password: Database password
    
    Returns:
        ThreadedConnectionPool object
    """
    connection_pool = psycopg2.pool.ThreadedConnectionPool(
        min_conn,
        max_conn,
        host=host,
        port=port,
        database=database,
        user=user,
        password=password,
    )
    return connection_pool


# Example usage with readers:
def example_usage():
    """Example of how to use the database connection with readers."""
    from src.infrastructure_layer.db_readers import (
        WalnutReader,
        WalnutImageReader,
    )
    
    # Create connection
    db_conn = create_db_connection(
        host="localhost",
        port=5432,
        database="walnut_pairing_db",
        user="postgres",
        password="your_password",
    )
    
    try:
        # Use with readers
        walnut_reader = WalnutReader(db_conn)
        walnut = walnut_reader.get_by_id("WALNUT-001")
        
        if walnut:
            print(f"Found walnut: {walnut.id} - {walnut.description}")
        
        # Get walnut with images
        walnut_with_images = walnut_reader.get_by_id_with_images("WALNUT-001")
        if walnut_with_images:
            print(f"Walnut has {len(walnut_with_images.images)} images")
    
    finally:
        # Always close the connection
        db_conn.close()


# Example with connection pool:
def example_usage_with_pool():
    """Example using connection pool."""
    from src.infrastructure_layer.db_readers import WalnutReader
    
    # Create connection pool
    pool = create_connection_pool(
        min_conn=1,
        max_conn=5,
        host="localhost",
        port=5432,
        database="walnut_pairing_db",
        user="postgres",
        password="your_password",
    )
    
    try:
        # Get connection from pool
        db_conn = pool.getconn()
        
        try:
            walnut_reader = WalnutReader(db_conn)
            walnuts = walnut_reader.get_all()
            print(f"Found {len(walnuts)} walnuts")
        finally:
            # Return connection to pool
            pool.putconn(db_conn)
    
    finally:
        # Close all connections in pool
        pool.closeall()


if __name__ == "__main__":
    # Example connection string format:
    # "host=localhost port=5432 dbname=walnut_pairing_db user=postgres password=mypassword"
    
    # Quick example:
    conn = create_db_connection(
        host="localhost",
        port=5432,
        database="walnut_pairing_db",
        user="postgres",
        password="postgres",  # Change to your password
    )
    print("Connection created successfully!")
    conn.close()

