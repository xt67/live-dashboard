import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine, text
from datetime import datetime
import time
import json
import numpy as np

# --- PostgreSQL Connection ---
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

# --- Streamlit Config ---
st.set_page_config(page_title="Universal Data Dashboard", layout="wide")
st.title("📊 Universal Data Dashboard")
st.write("⏱️ Auto-refreshes every 30 seconds. Works with ANY CSV/Excel data!")

# Initialize database tables
if 'db_initialized' not in st.session_state:
    with st.spinner("Setting up database..."):
        if ensure_tables_exist():
            st.session_state.db_initialized = True
        else:
            st.error("❌ Database setup failed. Please check your PostgreSQL connection.")
            st.stop()

# --- Handle Manual Refresh ---
if 'last_refresh' not in st.session_state:
    st.session_state['last_refresh'] = datetime.now()

if st.button("🔄 Manual Refresh Now"):
    st.session_state['last_refresh'] = datetime.now()
    st.cache_data.clear()

st.caption(f"Last refreshed: {st.session_state['last_refresh'].strftime('%Y-%m-%d %H:%M:%S')}")

# --- Load Available Data Sources ---
@st.cache_data(ttl=60)
def get_data_sources():
    try:
        query = "SELECT DISTINCT data_source FROM dashboard_data ORDER BY data_source"
        sources_df = pd.read_sql(query, engine)
        return sources_df['data_source'].tolist()
    except Exception as e:
        st.error(f"Database connection error: {e}")
        return []

# --- Load Column Metadata ---
@st.cache_data(ttl=60)
def get_column_metadata(source_name):
    try:
        query = text("SELECT column_info FROM data_source_metadata WHERE source_name = :source_name")
        with engine.connect() as conn:
            result = conn.execute(query, {'source_name': source_name}).fetchone()
            if result:
                metadata = result[0]
                if isinstance(metadata, str):
                    return json.loads(metadata)
                elif isinstance(metadata, dict):
                    return metadata
        return {}
    except Exception as e:
        st.error(f"Error loading metadata: {e}")
        return {}

# --- Load Data for Dashboard ---
@st.cache_data(ttl=30)
def load_dashboard_data(source_name, limit=1000):
    try:
        query = text("""
            SELECT record_timestamp, record_data 
            FROM dashboard_data 
            WHERE data_source = :source_name 
            ORDER BY record_timestamp DESC 
            LIMIT :limit
        """)
        
        with engine.connect() as conn:
            result = conn.execute(query, {'source_name': source_name, 'limit': limit})
            rows = result.fetchall()
        
        if not rows:
            return pd.DataFrame(), {}
        
        # Convert JSON data back to DataFrame
        data_records = []
        for row in rows:
            # Handle both string and dict formats for record_data
            record_data = row[1]  # record_data
            if isinstance(record_data, str):
                record = json.loads(record_data)
            elif isinstance(record_data, dict):
                record = record_data
            else:
                continue  # Skip invalid records
                
            record['_timestamp'] = row[0]  # Add timestamp
            data_records.append(record)
        
        if not data_records:
            return pd.DataFrame(), {}
        
        df = pd.DataFrame(data_records)
        
        # Get column metadata
        metadata = get_column_metadata(source_name)
        
        return df, metadata
        
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame(), {}

# --- Identify Chart Columns ---
def identify_chart_columns(df, metadata):
    """Safely identify the best columns for different chart types"""
    numeric_columns = []
    categorical_columns = []
    datetime_columns = []
    
    for col in df.columns:
        if col == '_timestamp':
            continue
            
        # First try metadata
        if col in metadata:
            col_type = metadata[col].get('data_type', 'text')
        else:
            # Fallback analysis - check actual data safely
            try:
                # Try to convert to numeric
                numeric_series = pd.to_numeric(df[col], errors='coerce')
                non_null_count = numeric_series.notna().sum()
                total_count = len(df[col])
                
                if total_count > 0 and non_null_count / total_count > 0.7:  # 70% can be converted
                    col_type = 'numeric'
                else:
                    try:
                        # Try datetime
                        datetime_series = pd.to_datetime(df[col], errors='coerce')
                        dt_non_null_count = datetime_series.notna().sum()
                        if total_count > 0 and dt_non_null_count / total_count > 0.7:
                            col_type = 'datetime'
                        else:
                            col_type = 'text'
                    except:
                        col_type = 'text'
            except:
                col_type = 'text'
        
        if col_type == 'numeric':
            numeric_columns.append(col)
        elif col_type == 'datetime':
            datetime_columns.append(col)
        else:
            categorical_columns.append(col)
    
    return numeric_columns, categorical_columns, datetime_columns

# --- Generate Charts Safely ---
def create_charts(df, metadata, source_name):
    """Create appropriate charts based on data structure with error handling"""
    if df.empty:
        st.warning("No data available for visualization")
        return
    
    numeric_cols, categorical_cols, datetime_cols = identify_chart_columns(df, metadata)
    
    st.write(f"**Detected columns:** Numeric: {len(numeric_cols)}, Categorical: {len(categorical_cols)}, DateTime: {len(datetime_cols)}")
    
    # Chart 1: Bar chart (categorical vs numeric)
    if categorical_cols and numeric_cols:
        st.subheader("📊 Category Analysis")
        
        col1, col2 = st.columns(2)
        with col1:
            cat_col = st.selectbox("Group by:", categorical_cols, key="cat_col")
        with col2:
            num_col = st.selectbox("Measure:", numeric_cols, key="num_col")
        
        if cat_col and num_col:
            try:
                # Safely aggregate data and ensure numeric conversion
                chart_df = df.copy()
                chart_df[num_col] = pd.to_numeric(chart_df[num_col], errors='coerce')
                
                # Remove rows where numeric conversion failed
                chart_df = chart_df.dropna(subset=[num_col])
                
                if len(chart_df) > 0:
                    chart_data = chart_df.groupby(cat_col)[num_col].sum().reset_index()
                    chart_data = chart_data.sort_values(num_col, ascending=False).head(20)  # Top 20
                    
                    fig = px.bar(chart_data, x=cat_col, y=num_col,
                                title=f"{num_col} by {cat_col}")
                    fig.update_layout(xaxis_tickangle=-45)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning(f"No valid numeric data found in column '{num_col}'")
            except Exception as e:
                st.error(f"Could not create bar chart: {e}")
    
    # Chart 2: Pie chart (distribution)
    if categorical_cols:
        st.subheader("🥧 Distribution Analysis")
        
        pie_cat_col = st.selectbox("Distribution of:", categorical_cols, key="pie_cat")
        
        if pie_cat_col:
            try:
                pie_data = df[pie_cat_col].value_counts().head(10).reset_index()
                pie_data.columns = [pie_cat_col, 'count']
                
                fig = px.pie(pie_data, values='count', names=pie_cat_col,
                            title=f"Distribution of {pie_cat_col}")
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Could not create pie chart: {e}")
    
    # Chart 3: Time series (if datetime columns exist)
    if datetime_cols and numeric_cols:
        st.subheader("📈 Time Series Analysis")
        
        col1, col2 = st.columns(2)
        with col1:
            date_col = st.selectbox("Date column:", datetime_cols + ['_timestamp'], key="date_col")
        with col2:
            ts_num_col = st.selectbox("Value column:", numeric_cols, key="ts_num_col")
        
        if date_col and ts_num_col:
            try:
                ts_df = df.copy()
                ts_df[ts_num_col] = pd.to_numeric(ts_df[ts_num_col], errors='coerce')
                
                if date_col != '_timestamp':
                    ts_df[date_col] = pd.to_datetime(ts_df[date_col], errors='coerce')
                    ts_df = ts_df.dropna(subset=[date_col, ts_num_col])
                    ts_df = ts_df.sort_values(date_col)
                else:
                    ts_df = ts_df.dropna(subset=[ts_num_col])
                    ts_df = ts_df.sort_values('_timestamp')
                    date_col = '_timestamp'
                
                if len(ts_df) > 0:
                    fig = px.line(ts_df, x=date_col, y=ts_num_col,
                                 title=f"{ts_num_col} over time")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("No valid data for time series")
            except Exception as e:
                st.error(f"Could not create time series chart: {e}")
    
    # Chart 4: Correlation heatmap (if multiple numeric columns)
    if len(numeric_cols) > 1:
        st.subheader("🔥 Correlation Analysis")
        
        try:
            # Calculate correlation matrix, ensuring all columns are actually numeric
            numeric_df = df[numeric_cols].copy()
            
            # Convert all columns to numeric, replacing non-numeric with NaN
            for col in numeric_cols:
                numeric_df[col] = pd.to_numeric(numeric_df[col], errors='coerce')
            
            # Drop columns that are all NaN after conversion
            numeric_df = numeric_df.dropna(axis=1, how='all')
            
            # Only calculate correlation if we have at least 2 columns with numeric data
            if len(numeric_df.columns) > 1 and len(numeric_df) > 1:
                corr_data = numeric_df.corr()
                
                fig = px.imshow(corr_data, 
                               labels=dict(color="Correlation"),
                               title="Correlation Matrix",
                               aspect="auto")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Not enough numeric data for correlation analysis")
        except Exception as e:
            st.warning(f"Could not generate correlation matrix: {e}")

# --- Main Dashboard ---
data_sources = get_data_sources()

if not data_sources:
    st.warning("No data sources found.")
    st.info("Import your data using: `streamlit run file_uploader.py`")
    st.code("python data_importer.py your_file.csv", language="bash")
else:
    # Source selection
    selected_source = st.selectbox("📁 Select Data Source:", data_sources)
    
    if selected_source:
        df, metadata = load_dashboard_data(selected_source)
        
        if not df.empty:
            # Display basic info
            st.success(f"✅ Loaded {len(df)} records from '{selected_source}'")
            
            # Debug info
            with st.expander("🔍 Debug Info"):
                st.write(f"DataFrame shape: {df.shape}")
                st.write(f"Columns: {list(df.columns)}")
                st.write(f"Metadata keys: {list(metadata.keys())}")
                if len(df) > 0:
                    st.write("Sample record:")
                    st.json(df.iloc[0].to_dict())
            
            # Show column info
            with st.expander("📋 Data Summary"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Columns:**")
                    for col in df.columns:
                        if col != '_timestamp':
                            col_type = metadata.get(col, {}).get('data_type', 'unknown')
                            unique_vals = df[col].nunique()
                            st.write(f"• {col} ({col_type}) - {unique_vals} unique values")
                
                with col2:
                    st.write("**Dataset Info:**")
                    st.write(f"• Total rows: {len(df)}")
                    st.write(f"• Total columns: {len(df.columns)-1}")  # Exclude timestamp
                    st.write(f"• Date range: {df['_timestamp'].min()} to {df['_timestamp'].max()}")
            
            # Raw data view
            st.subheader("📊 Raw Data")
            display_df = df.drop('_timestamp', axis=1) if '_timestamp' in df.columns else df
            st.dataframe(display_df.head(100), use_container_width=True)
            
            # Generate charts
            create_charts(df, metadata, selected_source)
            
        else:
            st.warning(f"No data found for source: {selected_source}")

# Note: Removed auto-refresh to prevent errors during development
# Add this back when everything is working: time.sleep(30); st.rerun()