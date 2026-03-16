import sqlite3
import os

db_path = r'f:\Labs\python\DriverTrack\drivetrack.db'

if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    exit(1)

connection = sqlite3.connect(db_path)
cursor = connection.cursor()

try:
    print("Adding 'is_favorite' column to 'vehicles' table...")
    cursor.execute("ALTER TABLE vehicles ADD COLUMN is_favorite BOOLEAN DEFAULT 0;")
    connection.commit()
    print("Column added successfully.")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e):
        print("Column 'is_favorite' already exists.")
    else:
        print(f"Error: {e}")
finally:
    connection.close()
