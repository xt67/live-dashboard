# Universal Data Dashboard

A completely flexible, real-time data dashboard built with Streamlit and PostgreSQL that automatically adapts to **ANY** CSV or Excel file structure. No configuration required - just import your data and the dashboard dynamically creates visualizations based on your data structure.

## ✨ Key Features

- � **Universal Data Support**: Works with ANY CSV/Excel file - sales, medical, financial, scientific, inventory, HR, etc.
- 🤖 **Automatic Data Type Detection**: Intelligently identifies numeric, text, and date columns
- 📈 **Dynamic Visualizations**: Automatically generates appropriate charts based on your data structure
- 🗄️ **Flexible Database Storage**: JSON-based storage adapts to any column structure
- ⏱️ **Real-time Updates**: Live dashboard with configurable refresh intervals
- � **Interactive Analysis**: Drill down with selectable columns for different chart types
- 📋 **Data Source Management**: Handle multiple datasets simultaneously

## 🚀 How It Works

1. **Import Any Data**: Point the tool to your CSV/Excel file
2. **Automatic Analysis**: The system analyzes your data structure and column types
3. **Dynamic Storage**: Data is stored in a flexible JSON-based database schema
4. **Smart Visualizations**: Dashboard automatically creates relevant charts based on your data
5. **Real-time Updates**: Watch your data come alive with live updates

## Prerequisites

- PostgreSQL server running on localhost:5432
- Database named `data_dashboard` with the flexible schema

### Database Setup

Run the provided SQL setup script to create the universal database structure:

```sql
-- Create database (run this manually first)
CREATE DATABASE data_dashboard;

-- Then run the setup script
\i database_setup.sql
```

Or copy and run the SQL from `database_setup.sql` in your PostgreSQL client.

## 📥 Installation & Setup

### Step 1: Setup PostgreSQL Database
1. Make sure PostgreSQL is installed and running on your computer
2. Create a database named `data_dashboard`
3. Run the database setup script:

```sql
-- In PostgreSQL command line or pgAdmin:
CREATE DATABASE data_dashboard;

-- Connect to the database, then run:
\i database_setup.sql
```

### Step 2: Install Dependencies
Open PowerShell/Command Prompt in your project folder and run:
```bash
pip install -r requirements.txt
```

### Step 3: Configure Database Connection
1. Copy `config_template.py` to `config.py`
2. Update `config.py` with your actual PostgreSQL credentials:
```python
DATABASE_CONFIG = {
    'host': 'localhost',
    'port': '5432',
    'username': 'postgres',
    'password': 'your_actual_password',  # Update this!
    'database': 'data_dashboard'
}
```

### Step 5: Launch the Dashboard
Run the universal data importer with any CSV or Excel file:
```bash
python data_importer.py
```
**Examples:**
```bash
python data_importer.py "C:\Users\Data\sales_report.xlsx"
python data_importer.py "C:\Downloads\patient_data.csv"
python data_importer.py "C:\Files\inventory_levels.csv"
```

The importer will:
1. Automatically analyze your data structure
2. Detect column types (numeric, text, dates)
3. Show you a summary of what it found
4. Store the data in the flexible database structure
5. Start real-time data insertion simulation

### Step 4: Launch the Dashboard
```bash
streamlit run dashboard_app.py
```

This opens your browser to `http://localhost:8501` where you can see your universal dashboard!

## 📊 Dashboard Features

The dashboard automatically adapts to your data and provides:

- **📋 Data Source Selection**: Choose from multiple imported datasets
- **📊 Category Analysis**: Interactive bar charts with selectable grouping and measure columns
- **🥧 Distribution Charts**: Pie charts showing distribution of categorical data
- **📈 Time Series**: Line charts for data with date/time columns
- **🔥 Correlation Analysis**: Heatmaps showing relationships between numeric columns
- **📋 Raw Data View**: Sortable, filterable table of your actual data
- **📊 Smart Column Detection**: Automatically identifies the best columns for each chart type

## 🎯 Quick Start Example

1. **Open PowerShell** and navigate to your project:
   ```bash
   cd "c:\Users\onlys\Documents\GitHub\live-dashboard-main"
   ```

2. **Install dependencies** (first time only):
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up database** (first time only):
   ```bash
   # Create database in PostgreSQL, then run:
   psql -d data_dashboard -f database_setup.sql
   ```

4. **Import any data file**:
   ```bash
   python data_importer.py
   # Enter your file path when prompted, e.g.: C:\Users\Data\my_data.xlsx
   ```

5. **Start the dashboard**:
   ```bash
   streamlit run dashboard_app.py
   ```

6. **View your dashboard** at: http://localhost:8501

## 🔧 Real-World Examples

The system works with ANY structured data. Here are some examples:

### 🏥 Hospital/Medical Data
```csv
Department,Procedure,Patient_Count,Cost,Date
Cardiology,Surgery,25,125000,2024-01-15
Emergency,Treatment,150,45000,2024-01-15
Radiology,MRI,75,89000,2024-01-15
```

### ⚡ Energy/Utilities Data  
```csv
Region,Meter_ID,Usage_kWh,Bill_Amount,Reading_Date
North,M001,1250,89.50,2024-01-01
South,M002,980,67.30,2024-01-01
East,M003,1580,112.75,2024-01-01
```

### 📦 Inventory/Warehouse Data
```csv
Warehouse,Product,Stock_Level,Value,Category
NYC,Widget A,500,12500,Electronics
LA,Widget B,300,7500,Tools
Chicago,Widget C,750,18750,Electronics
```

### 👥 HR/Employee Data
```csv
Department,Role,Headcount,Budget,Location
Engineering,Developer,25,2500000,Remote
Sales,Manager,15,1200000,Office
Marketing,Specialist,12,900000,Hybrid
```

### 📈 Financial/Trading Data
```csv
Symbol,Price,Volume,Market_Cap,Sector
AAPL,150.25,45000000,2400000000,Technology
GOOGL,2750.50,1200000,1800000000,Technology
TSLA,850.75,32000000,850000000,Automotive
```

**All work automatically!** No manual configuration needed.

## ⚙️ Configuration

### Database Connection
Update the PostgreSQL connection string in both files if your database settings differ:
```python
# In dashboard_app.py and data_importer.py:
engine = create_engine('postgresql://username:password@host:port/database_name')
```

### Refresh Intervals
- **Dashboard**: Auto-refreshes every 30 seconds
- **Data Import**: Default 1-second intervals (configurable during import)

## 🛠️ Advanced Features

### Multiple Data Sources
- Import multiple datasets with different structures
- Switch between data sources in the dashboard
- Each source maintains its own metadata and column information

### Intelligent Data Type Detection
- **Numeric**: Automatically detects integers, floats, percentages
- **Text/Categorical**: Identifies categories, names, locations
- **Dates**: Recognizes various date/time formats
- **Mixed**: Handles columns with mixed data types gracefully

### Smart Visualization Selection
The dashboard automatically chooses appropriate visualizations:
- **Bar Charts**: For categorical vs numeric data
- **Pie Charts**: For distribution analysis
- **Line Charts**: For time-series data
- **Heatmaps**: For correlation analysis between numeric columns

### Performance Optimization
- **Caching**: Intelligent data caching for better performance
- **Limits**: Automatic data limiting for large datasets
- **Indexing**: Database indexes for fast querying

## 🐛 Troubleshooting

### Common Issues

**Database Connection Error:**
```bash
# Check if PostgreSQL is running
# Verify database name and credentials
# Make sure the database_setup.sql has been run
```

**Import Fails:**
```bash
# Check file path and permissions
# Verify file format (CSV or Excel)
# Check for special characters in data
```

**No Data in Dashboard:**
```bash
# Make sure data import completed successfully
# Check database connection
# Verify the data source appears in the dropdown
```

### File Format Requirements
- **CSV**: Standard comma-separated format
- **Excel**: .xlsx or .xls format
- **Headers**: First row should contain column names
- **Data**: Subsequent rows contain actual data

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🤝 Contributing

Feel free to contribute to this project! The system is designed to be completely generic and extensible.

**Happy Data Visualization!** 📊✨=
