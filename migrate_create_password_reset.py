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
        # Check if table already exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='password_reset_tokens'")
        if cursor.fetchone():
            print("Table password_reset_tokens already exists.")
        else:
            print("Creating password_reset_tokens table...")
            cursor.execute("""
                CREATE TABLE password_reset_tokens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    otp_code VARCHAR(6) NOT NULL,
                    expires_at DATETIME NOT NULL,
                    is_used BOOLEAN NOT NULL DEFAULT 0,
                    created_at DATETIME NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            # Create indices
            cursor.execute("CREATE INDEX ix_password_reset_tokens_user_id ON password_reset_tokens (user_id)")
            cursor.execute("CREATE INDEX ix_password_reset_tokens_id ON password_reset_tokens (id)")
            print("Table password_reset_tokens created successfully.")

        conn.commit()

    except Exception as e:
        conn.rollback()
        print(f"Error during migration: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    run_migration()
