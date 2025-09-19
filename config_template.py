# Database Configuration Template
# Copy this file to config.py and update with your actual credentials

DATABASE_CONFIG = {
    'host': 'localhost',
    'port': '5432',
    'username': 'postgres',
    'password': 'your_password_here',  # Update with your actual password
    'database': 'data_dashboard'
}

# Alternative: Use environment variables for better security
# import os
# DATABASE_CONFIG = {
#     'host': os.getenv('DB_HOST', 'localhost'),
#     'port': os.getenv('DB_PORT', '5432'),
#     'username': os.getenv('DB_USER', 'postgres'),
#     'password': os.getenv('DB_PASSWORD'),
#     'database': os.getenv('DB_NAME', 'data_dashboard')
# }

# Connection string format:
# postgresql://username:password@host:port/database
def get_connection_string():
    return f"postgresql://{DATABASE_CONFIG['username']}:{DATABASE_CONFIG['password']}@{DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}/{DATABASE_CONFIG['database']}"