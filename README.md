<<<<<<< HEAD
# Live Data Dashboard

A real-time data dashboard built with Streamlit and PostgreSQL that allows you to import data from ANY CSV or Excel file and visualize it in real-time.

## Features

- 📊 Real-time data dashboard with auto-refresh
- 📁 Import data from **ANY** CSV or Excel file (no column mapping required!)
- 🤖 Automatic data type detection and visualization
- 📈 Interactive charts that adapt to your data
- 🗄️ PostgreSQL database integration
- ⏱️ Configurable data insertion intervals

## Prerequisites

- PostgreSQL server running on localhost:5432
- Database named `sales_dashboard` with a table called `sales_data`

### Database Setup

Create the database table with this SQL:

```sql
CREATE TABLE sales_data (
    id SERIAL PRIMARY KEY,
    region VARCHAR(50),
    product VARCHAR(100),
    quantity INTEGER,
    total_sales DECIMAL(10,2),
    sale_time TIMESTAMP
);
```

## How to Run

### Step 1: Setup PostgreSQL Database
1. Make sure PostgreSQL is installed and running on your computer
2. Create a database named `sales_dashboard`
3. Create the required table by running this SQL:

```sql
CREATE TABLE sales_data (
    id SERIAL PRIMARY KEY,
    region VARCHAR(50),
    product VARCHAR(100),
    quantity INTEGER,
    total_sales DECIMAL(10,2),
    sale_time TIMESTAMP
);
```

### Step 2: Install Dependencies
Open PowerShell/Command Prompt in your project folder and run:
```bash
pip install -r requirements.txt
```

### Step 3: Import Your Data
Run the data importer with your CSV or Excel file:
```bash
# Navigate to your project folder first
cd "c:\Users\onlys\Documents\GitHub\live dashboard"

# Then run the importer
python simulate_sales.py
```
The script will:
1. Load your file and automatically detect data types
2. Show you how it will organize your data
3. Ask for insertion delay (how fast to simulate real-time data)
4. Start inserting data into the dashboard

### Step 4: Start the Dashboard
In the same folder, run:
```bash
streamlit run dashboard_app.py
```

This will open your browser automatically to `http://localhost:8501` where you can see your live dashboard!

## Quick Start Example

1. **Open PowerShell** and navigate to your project:
   ```bash
   cd "c:\Users\onlys\Documents\GitHub\live dashboard"
   ```

2. **Install dependencies** (first time only):
   ```bash
   pip install -r requirements.txt
   ```

3. **Import data** from any CSV/Excel file:
   ```bash
   python simulate_sales.py
   ```
   Enter your file path when prompted (e.g., `C:\Users\onlys\Downloads\sales_data.xlsx`)

4. **Start the dashboard**:
   ```bash
   streamlit run dashboard_app.py
   ```

5. **View your dashboard** at: http://localhost:8501

## Advanced Usage

The system can now import data from **ANY** CSV or Excel file - no manual mapping required! It automatically detects:

- **Text columns** for grouping and categories
- **Numeric columns** for values and measurements
- **Data relationships** for meaningful visualizations

**Works with any data type:**
- 🏥 Hospital data (departments, procedures, costs, patient counts)
- ⚡ Electricity consumption (regions, meters, usage, costs)
- 🏪 Service data (locations, services, quantities, revenues)
- 📦 Inventory data (warehouses, products, stock levels, values)
- 👥 HR data (departments, roles, headcount, budgets)
- And literally any other structured data!

### Command Line Options

You can also specify the file path directly:
```bash
python simulate_sales.py "C:\Users\onlys\Downloads\my_data.csv"
python simulate_sales.py "C:\Users\onlys\Downloads\sales_report.xlsx"
```

### File Format Support

The system automatically adapts to any data structure:

### Hospital Data
```csv
Department,Procedure,Patient_Count,Cost
Cardiology,Surgery,25,125000
Emergency,Treatment,150,45000
```

### Electricity Consumption
```csv
Region,Meter_ID,Usage_kWh,Bill_Amount
North,M001,1250,89.50
South,M002,980,67.30
```

### Service Business
```csv
Location,Service_Type,Sessions,Revenue
Downtown,Consultation,15,3750
Uptown,Training,8,2400
```

### Inventory Management
```csv
Warehouse,Product,Stock_Level,Value
NYC,Widget A,500,12500
LA,Widget B,300,7500
```

**All of these work automatically!** No manual mapping needed.

## Configuration

Update the PostgreSQL connection string in both files if needed:
```python
engine = create_engine('postgresql://username:password@host:port/database_name')
```
=======