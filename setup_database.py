#!/usr/bin/env python3
"""
Database Setup Script for Universal Data Dashboard
This script creates the necessary database structure for the universal dashboard.
"""

import os
import sys
from sqlalchemy import create_engine, text

def setup_database():
    """Set up the database with the required schema"""
    
    print("=== Universal Data Dashboard Database Setup ===")
    print()
    
    # Database connection details
    default_host = "localhost"
    default_port = "5432"
    default_user = "postgres"
    default_password = "1693"
    default_database = "data_dashboard"
    
    print("Enter your PostgreSQL connection details:")
    host = input(f"Host (default: {default_host}): ").strip() or default_host
    port = input(f"Port (default: {default_port}): ").strip() or default_port
    user = input(f"Username (default: {default_user}): ").strip() or default_user
    password = input(f"Password (default: {default_password}): ").strip() or default_password
    database = input(f"Database name (default: {default_database}): ").strip() or default_database
    
    # Create connection string
    connection_string = f"postgresql://{user}:{password}@{host}:{port}/{database}"
    
    try:
        print(f"\nConnecting to database: {database}")
        engine = create_engine(connection_string)
        
        # Read and execute the SQL setup script
        sql_file_path = os.path.join(os.path.dirname(__file__), 'database_setup.sql')
        
        if not os.path.exists(sql_file_path):
            print(f"Error: Could not find database_setup.sql in {os.path.dirname(__file__)}")
            return False
        
        with open(sql_file_path, 'r') as f:
            sql_script = f.read()
        
        print("Executing database setup script...")
        
        with engine.connect() as conn:
            # Split the script into individual statements
            statements = [stmt.strip() for stmt in sql_script.split(';') if stmt.strip()]
            
            for statement in statements:
                if statement:
                    try:
                        conn.execute(text(statement))
                        print(f"✓ Executed: {statement[:50]}...")
                    except Exception as e:
                        if "already exists" in str(e).lower():
                            print(f"⚠ Already exists: {statement[:50]}...")
                        else:
                            print(f"✗ Error: {e}")
            
            conn.commit()
        
        print("\n✅ Database setup completed successfully!")
        print(f"Your database '{database}' is ready for the Universal Data Dashboard.")
        print("\nNext steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Import data: python data_importer.py your_file.csv")
        print("3. Start dashboard: streamlit run dashboard_app.py")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Database setup failed: {e}")
        print("\nPlease check:")
        print("1. PostgreSQL is running")
        print("2. Database exists (create it manually if needed)")
        print("3. Connection credentials are correct")
        print("4. User has necessary permissions")
        return False

if __name__ == "__main__":
    success = setup_database()
    sys.exit(0 if success else 1)