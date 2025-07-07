import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine
from datetime import datetime
import time

# --- PostgreSQL Connection ---
engine = create_engine('postgresql://postgres:1693@localhost:5432/sales_dashboard')

# --- Streamlit Config ---
st.set_page_config(page_title="Live Data Dashboard", layout="wide")
st.title("📊 Real-Time Data Dashboard")
st.write("⏱️ Auto-refreshes every 60 seconds. Click the button below to manually refresh.")

# --- Handle Manual Refresh ---
if 'last_refresh' not in st.session_state:
    st.session_state['last_refresh'] = datetime.now()

if st.button("🔄 Manual Refresh Now"):
    st.session_state['last_refresh'] = datetime.now()

st.caption(f"Last refreshed: {st.session_state['last_refresh'].strftime('%Y-%m-%d %H:%M:%S')}")

# --- Load Data ---
@st.cache_data(ttl=60)
def load_data():
    query = "SELECT * FROM sales_data ORDER BY sale_time DESC LIMIT 100;"
    df = pd.read_sql(query, engine)
    return df

df = load_data()

if len(df) > 0:
    # --- Display Data ---
    st.subheader("Recent Data")
    st.dataframe(df)

    # --- Charts ---
    st.subheader("Data by Category")
    fig = px.bar(df, x='product', y='total_sales', color='region', 
                title="Values by Category")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Distribution Overview")
    region_data = df.groupby("region")["total_sales"].sum().reset_index()
    fig2 = px.pie(region_data, values="total_sales", names="region", 
                 title="Distribution by Groups")
    st.plotly_chart(fig2, use_container_width=True)
else:
    st.warning("No data available. Please run the data importer first.")
    st.info("Run: `python simulate_sales.py` to import your CSV/Excel data.")

# --- Auto Refresh (every 60 seconds) ---
time.sleep(60)
st.rerun()
