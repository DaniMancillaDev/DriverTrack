import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "drivetrack.db")

def migrate():
    print(f"Connecting to {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE maintenances ADD COLUMN category VARCHAR(50) DEFAULT 'General';")
        conn.commit()
        print("Column 'category' added to 'maintenances' successfully.")
    except sqlite3.OperationalError as e:
        print(f"Migration error (might already exist): {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
