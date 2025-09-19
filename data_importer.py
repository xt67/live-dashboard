import pandas as pd
import time
import os
import sys
import json
from datetime import datetime
from sqlalchemy import create_engine, text
from pathlib import Path
import numpy as np

# Connect to PostgreSQL
engine = create_engine('postgresql://postgres:1693@localhost:5432/data_dashboard')

def load_data_from_file(file_path):
    """Load data from CSV or Excel file with automatic encoding detection"""
    file_extension = Path(file_path).suffix.lower()
    try:
        if file_extension == '.csv':
            # Try different encodings for CSV files
            encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252', 'utf-16']
            df = None
            
            for encoding in encodings:
                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                    print(f"✅ Successfully loaded CSV with {encoding} encoding")
                    break
                except UnicodeDecodeError:
                    print(f"❌ Failed with {encoding} encoding, trying next...")
                    continue
                except Exception as e:
                    if encoding == encodings[-1]:  # Last encoding
                        raise e
                    continue
            
            if df is None:
                raise ValueError("Could not decode the CSV file with any supported encoding")
                
        elif file_extension in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_extension}. Please use CSV or Excel files.")
        
        print(f"Successfully loaded {len(df)} rows with {len(df.columns)} columns")
        print(f"Columns: {list(df.columns)}")
        return df
    
    except Exception as e:
        print(f"Error loading file: {e}")
        print("\nTroubleshooting tips:")
        print("1. Check if the file is not corrupted")
        print("2. Try opening the file in Excel first to verify it's valid")
        print("3. For CSV files, try saving it as UTF-8 encoded CSV from Excel")
        print("4. Make sure the file is not currently open in another program")
        return None

def analyze_data_structure(df):
    """Analyze the structure of the data and determine column types"""
    print("\n=== Data Structure Analysis ===")
    
    column_info = {}
    
    for col in df.columns:
        # Clean column name
        clean_col = str(col).strip()
        
        # Analyze data types and content
        series = df[col]
        non_null_series = series.dropna()
        
        # Try to determine the best data type
        column_stats = {
            'original_name': clean_col,
            'total_rows': len(series),
            'non_null_rows': len(non_null_series),
            'null_percentage': (len(series) - len(non_null_series)) / len(series) * 100,
            'unique_values': len(non_null_series.unique()),
            'data_type': 'text'  # default
        }
        
        if len(non_null_series) > 0:
            # Try numeric conversion
            try:
                numeric_series = pd.to_numeric(non_null_series, errors='coerce')
                numeric_non_null = numeric_series.dropna()
                
                if len(numeric_non_null) / len(non_null_series) > 0.8:  # 80% can be converted to numeric
                    column_stats['data_type'] = 'numeric'
                    column_stats['min_value'] = float(numeric_non_null.min())
                    column_stats['max_value'] = float(numeric_non_null.max())
                    column_stats['mean_value'] = float(numeric_non_null.mean())
                else:
                    # Check if it's datetime
                    try:
                        datetime_series = pd.to_datetime(non_null_series, errors='coerce')
                        datetime_non_null = datetime_series.dropna()
                        
                        if len(datetime_non_null) / len(non_null_series) > 0.8:
                            column_stats['data_type'] = 'datetime'
                        else:
                            column_stats['data_type'] = 'text'
                            # For text, get sample values
                            sample_values = non_null_series.value_counts().head(5)
                            column_stats['top_values'] = sample_values.to_dict()
                    except:
                        column_stats['data_type'] = 'text'
                        sample_values = non_null_series.value_counts().head(5)
                        column_stats['top_values'] = sample_values.to_dict()
            except:
                column_stats['data_type'] = 'text'
                sample_values = non_null_series.value_counts().head(5)
                column_stats['top_values'] = sample_values.to_dict()
        
        column_info[clean_col] = column_stats
        
        # Print analysis
        print(f"\nColumn: {clean_col}")
        print(f"  Type: {column_stats['data_type']}")
        print(f"  Non-null: {column_stats['non_null_rows']}/{column_stats['total_rows']} ({100-column_stats['null_percentage']:.1f}%)")
        print(f"  Unique values: {column_stats['unique_values']}")
        
        if column_stats['data_type'] == 'numeric':
            print(f"  Range: {column_stats['min_value']:.2f} to {column_stats['max_value']:.2f}")
            print(f"  Average: {column_stats['mean_value']:.2f}")
        elif column_stats['data_type'] == 'text' and 'top_values' in column_stats:
            print(f"  Top values: {list(column_stats['top_values'].keys())[:3]}")
    
    return column_info

def prepare_data_for_storage(df, source_name):
    """Prepare data for storage in the generic database structure"""
    print(f"\n=== Preparing Data for Storage ===")
    
    prepared_records = []
    
    for index, row in df.iterrows():
        # Convert the entire row to a JSON-serializable dictionary
        record_data = {}
        
        for col in df.columns:
            value = row[col]
            
            # Handle different data types for JSON storage
            if pd.isna(value):
                record_data[str(col)] = None
            elif isinstance(value, (np.int64, np.int32, int)):
                record_data[str(col)] = int(value)
            elif isinstance(value, (np.float64, np.float32, float)):
                if np.isnan(value):
                    record_data[str(col)] = None
                else:
                    record_data[str(col)] = float(value)
            elif isinstance(value, (pd.Timestamp, datetime)):
                record_data[str(col)] = value.isoformat() if pd.notna(value) else None
            else:
                record_data[str(col)] = str(value)
        
        prepared_records.append({
            'data_source': source_name,
            'record_data': record_data
        })
    
    print(f"Prepared {len(prepared_records)} records for storage")
    return prepared_records

def store_column_metadata(source_name, column_info):
    """Store column metadata for the data source"""
    try:
        with engine.connect() as conn:
            # Check if metadata already exists
            check_query = text("SELECT id FROM data_source_metadata WHERE source_name = :source_name")
            result = conn.execute(check_query, {'source_name': source_name}).fetchone()
            
            if result:
                # Update existing metadata
                update_query = text("""
                    UPDATE data_source_metadata 
                    SET column_info = :column_info, updated_at = CURRENT_TIMESTAMP
                    WHERE source_name = :source_name
                """)
                conn.execute(update_query, {
                    'source_name': source_name,
                    'column_info': json.dumps(column_info)
                })
                print(f"Updated metadata for source: {source_name}")
            else:
                # Insert new metadata
                insert_query = text("""
                    INSERT INTO data_source_metadata (source_name, column_info)
                    VALUES (:source_name, :column_info)
                """)
                conn.execute(insert_query, {
                    'source_name': source_name,
                    'column_info': json.dumps(column_info)
                })
                print(f"Stored metadata for new source: {source_name}")
            
            conn.commit()
            
    except Exception as e:
        print(f"Error storing metadata: {e}")

def insert_data_to_db(prepared_records, delay_seconds=60):
    """Insert prepared records to database with specified delay"""
    print(f"Starting to insert {len(prepared_records)} records with {delay_seconds} second intervals...")
    print("Press Ctrl+C to stop.")
    
    for index, record in enumerate(prepared_records):
        try:
            insert_query = text("""
                INSERT INTO dashboard_data (data_source, record_data)
                VALUES (:data_source, :record_data)
            """)
            
            with engine.connect() as conn:
                conn.execute(insert_query, {
                    'data_source': record['data_source'],
                    'record_data': json.dumps(record['record_data'])
                })
                conn.commit()
                
            print(f"Inserted record {index + 1}/{len(prepared_records)}: {record['data_source']}")
            
            # Wait before next insertion (except for the last record)
            if index < len(prepared_records) - 1:
                time.sleep(delay_seconds)
        
        except Exception as e:
            print(f"Error inserting record {index + 1}: {e}")
            continue
    
    print("All records have been inserted!")

def main():
    print("=== Generic Data Importer ===")
    print("This tool imports data from ANY CSV or Excel file into a flexible dashboard.")
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
    
    # Analyze data structure
    source_name = Path(file_path).stem  # Use filename without extension as source name
    column_info = analyze_data_structure(df)
    
    # Store column metadata
    store_column_metadata(source_name, column_info)
    
    # Prepare data for storage
    prepared_records = prepare_data_for_storage(df, source_name)
    if not prepared_records:
        return
    
    print(f"\nData source name: {source_name}")
    print("Your data will be stored with full flexibility for dynamic dashboard visualization.")
    
    # Get delay interval
    try:
        delay = input("\nEnter delay between insertions in seconds (default: 1): ").strip()
        delay = int(delay) if delay else 1
    except ValueError:
        delay = 1
    
    # Confirm before proceeding
    confirm = input(f"\nReady to insert {len(prepared_records)} records with {delay} second intervals. Continue? (y/N): ").strip().lower()
    if confirm != 'y':
        print("Operation cancelled.")
        return
    
    # Insert data
    try:
        insert_data_to_db(prepared_records, delay)
        print(f"\n✅ Successfully imported data from '{source_name}'!")
        print("You can now start the dashboard to view your data.")
    except KeyboardInterrupt:
        print("\n\nOperation stopped by user.")
    except Exception as e:
        print(f"\nError during insertion: {e}")

if __name__ == "__main__":
    main()