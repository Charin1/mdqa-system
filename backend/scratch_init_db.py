from app.db.sqlite_db import init_db
import sys
import os

# Add current directory to path so we can import app
sys.path.append(os.getcwd())

try:
    print("Initializing database...")
    init_db()
    print("Database initialized successfully.")
except Exception as e:
    print(f"Error initializing database: {e}")
    sys.exit(1)
