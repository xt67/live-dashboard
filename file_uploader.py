import streamlit as st
import pandas as pd
import time
import os
import json
from datetime import datetime
from sqlalchemy import create_engine, text
from pathlib import Path
import numpy as np
import tempfile

# Connect to PostgreSQL
# TODO: Update with your actual database credentials
engine = create_engine('postgresql://postgres:your_password@localhost:5432/data_dashboard')

def ensure_tables_exist():
    """Create database tables if they don't exist"""
    try:
        with engine.connect() as conn:
            # Create dashboard_data table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS dashboard_data (
                    id SERIAL PRIMARY KEY,
                    record_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    data_source VARCHAR(255),
                    record_data JSONB
                );
            """))
            
            # Create data_source_metadata table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS data_source_metadata (
                    id SERIAL PRIMARY KEY,
                    source_name VARCHAR(255) UNIQUE NOT NULL,
                    column_info JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """))
            
            # Create indexes
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_dashboard_data_timestamp 
                ON dashboard_data(record_timestamp);
            """))
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_dashboard_data_source 
                ON dashboard_data(data_source);
            """))
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_dashboard_data_jsonb 
                ON dashboard_data USING GIN(record_data);
            """))
            
            conn.commit()
            return True
    except Exception as e:
        st.error(f"Database setup error: {e}")
        return False

st.set_page_config(page_title="Universal Data Importer", layout="wide")
st.title("📁 Universal Data Importer")
st.write("Upload any CSV or Excel file and import it into your dashboard!")

# Initialize database tables
if 'db_initialized' not in st.session_state:
    with st.spinner("Setting up database..."):
        if ensure_tables_exist():
            st.session_state.db_initialized = True
            st.success("✅ Database ready!")
        else:
            st.error("❌ Database setup failed. Please check your PostgreSQL connection.")
            st.stop()

def analyze_data_structure(df):
    """Analyze the structure of the data and determine column types"""
    st.subheader("📊 Data Structure Analysis")
    
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
                        datetime_series = pd.to_datetime(non_null_series, errors='coerce', infer_datetime_format=True)
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
    
    # Display analysis in a nice table
    analysis_data = []
    for col, stats in column_info.items():
        row = {
            'Column': col,
            'Type': stats['data_type'],
            'Non-null': f"{stats['non_null_rows']}/{stats['total_rows']} ({100-stats['null_percentage']:.1f}%)",
            'Unique Values': stats['unique_values']
        }
        
        if stats['data_type'] == 'numeric':
            row['Range/Sample'] = f"{stats['min_value']:.2f} to {stats['max_value']:.2f}"
        elif stats['data_type'] == 'text' and 'top_values' in stats:
            row['Range/Sample'] = f"Top: {list(stats['top_values'].keys())[:2]}"
        else:
            row['Range/Sample'] = "Various"
            
        analysis_data.append(row)
    
    st.dataframe(analysis_data, use_container_width=True)
    
    return column_info

def prepare_data_for_storage(df, source_name):
    """Prepare data for storage in the generic database structure"""
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
                st.success(f"Updated metadata for source: {source_name}")
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
                st.success(f"Stored metadata for new source: {source_name}")
            
            conn.commit()
            
    except Exception as e:
        st.error(f"Error storing metadata: {e}")

def insert_data_to_db(prepared_records, delay_seconds=1):
    """Insert prepared records to database with specified delay"""
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
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
                
            # Update progress
            progress = (index + 1) / len(prepared_records)
            progress_bar.progress(progress)
            status_text.text(f"Inserted record {index + 1}/{len(prepared_records)}")
            
            # Wait before next insertion (except for the last record)
            if index < len(prepared_records) - 1:
                time.sleep(delay_seconds)
        
        except Exception as e:
            st.error(f"Error inserting record {index + 1}: {e}")
            continue
    
    status_text.text("✅ All records have been inserted!")

# Main UI
uploaded_file = st.file_uploader(
    "Choose a CSV or Excel file",
    type=['csv', 'xlsx', 'xls'],
    help="Upload any CSV or Excel file with structured data"
)

if uploaded_file is not None:
    # Get file details
    file_details = {
        "filename": uploaded_file.name,
        "filetype": uploaded_file.type,
        "filesize": uploaded_file.size
    }
    
    st.write("📄 **File Details:**")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Filename", file_details["filename"])
    with col2:
        st.metric("File Type", file_details["filetype"])
    with col3:
        st.metric("File Size", f"{file_details['filesize']:,} bytes")
    
    try:
        # Load the data with encoding detection
        if uploaded_file.name.endswith('.csv'):
            # Try different encodings for CSV files
            encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252', 'utf-16']
            df = None
            
            for encoding in encodings:
                try:
                    uploaded_file.seek(0)  # Reset file pointer
                    df = pd.read_csv(uploaded_file, encoding=encoding)
                    st.info(f"✅ Successfully loaded CSV with {encoding} encoding")
                    break
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    if encoding == encodings[-1]:  # Last encoding
                        raise e
                    continue
            
            if df is None:
                raise ValueError("Could not decode the CSV file with any supported encoding")
        else:
            df = pd.read_excel(uploaded_file)
        
        st.success(f"✅ Successfully loaded {len(df)} rows with {len(df.columns)} columns")
        
        # Show preview
        st.subheader("📋 Data Preview")
        st.dataframe(df.head(), use_container_width=True)
        
        # Analyze data structure
        source_name = Path(uploaded_file.name).stem
        column_info = analyze_data_structure(df)
        
        # Import settings
        st.subheader("⚙️ Import Settings")
        col1, col2 = st.columns(2)
        
        with col1:
            source_name = st.text_input("Data Source Name", value=source_name, help="Name for this dataset in the dashboard")
        
        with col2:
            delay = st.number_input("Delay between records (seconds)", min_value=0.1, max_value=10.0, value=1.0, step=0.1, 
                                  help="Simulates real-time data streaming")
        
        # Import button
        if st.button("🚀 Import Data to Dashboard", type="primary"):
            if source_name:
                with st.spinner("Importing data..."):
                    # Store column metadata
                    store_column_metadata(source_name, column_info)
                    
                    # Prepare data for storage
                    prepared_records = prepare_data_for_storage(df, source_name)
                    
                    # Insert data
                    insert_data_to_db(prepared_records, delay)
                    
                    st.success("🎉 Data import completed successfully!")
                    st.info("You can now view your data in the dashboard: `streamlit run dashboard_app.py`")
            else:
                st.error("Please provide a data source name")
    
    except UnicodeDecodeError as e:
        st.error("❌ **Encoding Error:** The file contains characters that can't be read with standard encoding.")
        st.info("🛠️ **Solutions:**")
        st.markdown("""
        1. **Open the file in Excel** and save it as "CSV UTF-8 (Comma delimited)"
        2. **Try a different file format** - if it's CSV, try saving as Excel (.xlsx)
        3. **Check for special characters** in your data that might cause encoding issues
        4. **Contact support** if the issue persists
        """)
        
    except Exception as e:
        st.error(f"❌ **Error loading file:** {e}")
        st.info("🛠️ **Troubleshooting:**")
        st.markdown("""
        - Make sure your file is a valid CSV or Excel file
        - Check that the file isn't corrupted or password-protected
        - Verify the file has proper column headers in the first row
        - Try opening the file in Excel first to verify it's readable
        - Make sure the file isn't currently open in another program
        """)

else:
    st.info("👆 Please upload a CSV or Excel file to get started")
    
    # Show some example formats
    st.subheader("📝 Example File Formats")
    
    tab1, tab2, tab3 = st.tabs(["Sales Data", "Medical Data", "Inventory Data"])
    
    with tab1:
        st.code("""Region,Product,Quantity,Revenue,Date
North,Widget A,150,15000,2024-01-15
South,Widget B,200,18000,2024-01-15
East,Widget A,175,17500,2024-01-15""", language="csv")
    
    with tab2:
        st.code("""Department,Procedure,Patient_Count,Cost
Cardiology,Surgery,25,125000
Emergency,Treatment,150,45000
Radiology,MRI,75,89000""", language="csv")
    
    with tab3:
        st.code("""Warehouse,Product,Stock_Level,Value
NYC,Widget A,500,12500
LA,Widget B,300,7500
Chicago,Widget C,750,18750""", language="csv")

# Footer
st.markdown("---")
st.markdown("💡 **Tip:** After importing, run `streamlit run dashboard_app.py` to view your data!")