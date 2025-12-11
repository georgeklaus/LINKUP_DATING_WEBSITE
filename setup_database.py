import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os
import sys

def setup_database():
    """Create database and user for the dating app"""
    
    # Connect to PostgreSQL default database
    try:
        conn = psycopg2.connect(
            dbname='postgres',
            user='postgres',
            password='postgres',
            host='localhost',
            port='5432'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Create database
        cursor.execute("CREATE DATABASE dating_app_db;")
        print("Database 'dating_app_db' created successfully")
        
        # Create user
        cursor.execute("CREATE USER dating_app_user WITH PASSWORD 'dating123';")
        print("User 'dating_app_user' created successfully")
        
        # Grant privileges
        cursor.execute("GRANT ALL PRIVILEGES ON DATABASE dating_app_db TO dating_app_user;")
        print("Privileges granted successfully")
        
        cursor.close()
        conn.close()
        
        print("Database setup completed successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure PostgreSQL is running and credentials are correct")

if __name__ == "__main__":
    setup_database()