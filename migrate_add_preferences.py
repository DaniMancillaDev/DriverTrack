import sqlite3
import os

db_path = '/home/danimancilla/Escritorio/labs/python/DriverTrack/drivetrack.db'

def run_migration():
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if columns are already there
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'pref_push_notifications' not in columns:
            print("Adding pref_push_notifications to users...")
            cursor.execute("ALTER TABLE users ADD COLUMN pref_push_notifications BOOLEAN NOT NULL DEFAULT 1")
            
        if 'pref_service_reminders' not in columns:
            print("Adding pref_service_reminders to users...")
            cursor.execute("ALTER TABLE users ADD COLUMN pref_service_reminders BOOLEAN NOT NULL DEFAULT 1")
            
        if 'pref_critical_alerts' not in columns:
            print("Adding pref_critical_alerts to users...")
            cursor.execute("ALTER TABLE users ADD COLUMN pref_critical_alerts BOOLEAN NOT NULL DEFAULT 1")

        conn.commit()
        print("Migration complete. Added preference columns to users table.")

    except Exception as e:
        conn.rollback()
        print(f"Error during migration: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    run_migration()
