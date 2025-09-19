import pandas as pd
import time
import os
import sys
from datetime import datetime
from sqlalchemy import create_engine, text
from pathlib import Path

# Connect to PostgreSQL
engine = create_engine('postgresql://postgres:1693@localhost:5432/sales_dashboard')

def load_data_from_file(file_path):
    """Load data from CSV or Excel file"""
    file_extension = Path(file_path).suffix.lower()
    try:
        if file_extension == '.csv':
            df = pd.read_csv(file_path)
        elif file_extension in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_extension}. Please use CSV or Excel files.")
        
        print(f"Available columns in your file: {list(df.columns)}")
        return df
    
    except Exception as e:
        print(f"Error loading file: {e}")
        return None

def prepare_data_for_dashboard(df):
    """Prepare any data for the dashboard by creating flexible mappings"""
    print("\n=== Data Preparation ===")
    print("Your data will be displayed in the dashboard as-is.")
    print("The system will automatically detect the best columns for visualization.")
    
    # Display available columns
    print(f"\nAvailable columns in your data:")
    for i, col in enumerate(df.columns, 1):
        print(f"  {i}. {col}")
    
    # Automatically detect column types
    text_columns = []
    numeric_columns = []
    
    for col in df.columns:
        # Try to convert to numeric
        numeric_data = pd.to_numeric(df[col], errors='coerce')
        non_null_numeric = numeric_data.dropna()
        
        # If more than 50% of data is numeric, consider it numeric
        if len(non_null_numeric) > len(df) * 0.5:
            numeric_columns.append(col)
        else:
            text_columns.append(col)
    
    print(f"\nDetected text columns (for grouping): {text_columns}")
    print(f"Detected numeric columns (for values): {numeric_columns}")
    
    # Create a standardized format for the dashboard
    # Use the first text column as "category1", second as "category2", etc.
    # Use numeric columns as-is
    
    dashboard_df = pd.DataFrame()
    
    # Add text columns (categories)
    if len(text_columns) >= 1:
        dashboard_df['category1'] = df[text_columns[0]].astype(str)
        print(f"Primary grouping: {text_columns[0]} → category1")
    
    if len(text_columns) >= 2:
        dashboard_df['category2'] = df[text_columns[1]].astype(str)
        print(f"Secondary grouping: {text_columns[1]} → category2")
    
    # Add numeric columns
    for i, col in enumerate(numeric_columns[:2]):  # Take first 2 numeric columns
        dashboard_df[f'value{i+1}'] = pd.to_numeric(df[col], errors='coerce')
        print(f"Value {i+1}: {col} → value{i+1}")
    
    # If we don't have enough data, create defaults
    if 'category1' not in dashboard_df.columns:
        dashboard_df['category1'] = 'Data'
    
    if 'category2' not in dashboard_df.columns:
        dashboard_df['category2'] = df.columns[0] if len(df.columns) > 0 else 'Item'
    
    if 'value1' not in dashboard_df.columns:
        # Use the first numeric-like column or create a count
        dashboard_df['value1'] = 1
    
    if 'value2' not in dashboard_df.columns:
        # Use the second numeric column or duplicate the first
        dashboard_df['value2'] = dashboard_df['value1'] if 'value1' in dashboard_df.columns else 1
    
    # Remove rows with all NaN values
    dashboard_df = dashboard_df.dropna(how='all')
    
    # Store original column mappings for reference
    dashboard_df.attrs['original_columns'] = {
        'category1': text_columns[0] if len(text_columns) >= 1 else 'Generated',
        'category2': text_columns[1] if len(text_columns) >= 2 else 'Generated',
        'value1': numeric_columns[0] if len(numeric_columns) >= 1 else 'Generated',
        'value2': numeric_columns[1] if len(numeric_columns) >= 2 else 'Generated'
    }
    
    print(f"\nSuccessfully prepared {len(dashboard_df)} records for dashboard.")
    return dashboard_df

def insert_data_to_db(df, delay_seconds=60):
    """Insert data from DataFrame to database with specified delay"""
    print(f"Starting to insert {len(df)} records with {delay_seconds} second intervals...")
    print("Press Ctrl+C to stop.")
    
    for index, row in df.iterrows():
        try:
            # Add current timestamp for sale_time
            insert_query = text("""
                INSERT INTO sales_data (region, product, quantity, total_sales, sale_time)
                VALUES (:region, :product, :quantity, :total_sales, :sale_time)
            """)
            
            with engine.connect() as conn:
                conn.execute(insert_query, {
                    'region': row['category1'],
                    'product': row['category2'],
                    'quantity': int(row['value1']) if pd.notna(row['value1']) else 1,
                    'total_sales': float(row['value2']) if pd.notna(row['value2']) else 0.0,
                    'sale_time': datetime.now()
                })
                conn.commit()
                
            print(f"Inserted record {index + 1}/{len(df)}: {row['category1']}, {row['category2']}, {row['value1']}, {row['value2']}")
            
            # Wait before next insertion (except for the last record)
            if index < len(df) - 1:
                time.sleep(delay_seconds)
        
        except Exception as e:
            print(f"Error inserting record {index + 1}: {e}")
            continue
    
    print("All records have been inserted!")

def main():
    print("=== Sales Data Importer ===")
    print("This tool imports sales data from CSV or Excel files into the database.")
    print()
    
    # Get file path from user
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = input("Enter the path to your CSV or Excel file: ").strip().strip('"')
    
    # Check if file exists
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        return
    
    # Load data from file
    df = load_data_from_file(file_path)
    if df is None:
        return
    
    print(f"\nSuccessfully loaded {len(df)} records from {file_path}")
    print("\nFirst 5 rows of your data:")
    print(df.head())
    
    # Automatically prepare data for dashboard
    prepared_df = prepare_data_for_dashboard(df)
    if prepared_df is None:
        return
    
    print("\nPrepared data preview:")
    print(prepared_df.head())
    
    # Get delay interval
    try:
        delay = input("\nEnter delay between insertions in seconds (default: 60): ").strip()
        delay = int(delay) if delay else 60
    except ValueError:
        delay = 60
    
    # Confirm before proceeding
    confirm = input(f"\nReady to insert {len(prepared_df)} records with {delay} second intervals. Continue? (y/N): ").strip().lower()
    if confirm != 'y':
        print("Operation cancelled.")
        return
    
    # Insert data
    try:
        insert_data_to_db(prepared_df, delay)
    except KeyboardInterrupt:
        print("\n\nOperation stopped by user.")
    except Exception as e:
        print(f"\nError during insertion: {e}")

if __name__ == "__main__":
    main()