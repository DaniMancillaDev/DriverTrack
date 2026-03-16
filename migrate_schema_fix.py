import sqlite3
import os

db_path = '/home/danim/Escritorio/Labs/Python/DriveTrack/drivetrack.db'

def fix_schema():
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 1. Ensure catalogue exists and is populated
        print("Ensuring vehicle types catalogue exists...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS vehicle_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT UNIQUE NOT NULL,
            label TEXT NOT NULL,
            icon TEXT NOT NULL,
            image_url TEXT NOT NULL
        )
        """)

        types = [
            ('car', 'Car', 'directions_car_filled_rounded', 'https://images.unsplash.com/photo-1494976388531-d1058494cdd8?auto=format&fit=crop&q=80&w=1000'),
            ('moto', 'Motorcycle', 'motorcycle_rounded', 'https://images.unsplash.com/photo-1558981403-c5f91cbba527?auto=format&fit=crop&q=80&w=1000')
        ]
        for t in types:
            cursor.execute("INSERT OR IGNORE INTO vehicle_types (slug, label, icon, image_url) VALUES (?, ?, ?, ?)", t)
        
        conn.commit()
        print("Catalogue check complete.")

        # 2. Check current schema for vehicles table
        cursor.execute("PRAGMA table_info(vehicles)")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"Current columns in 'vehicles': {columns}")

        if 'type' not in columns:
            print("Vehicles table already has the correct schema. Done.")
            return

        print("Starting 'copy-and-swap' migration to remove 'type' column...")

        # 3. Create new table with the correct schema
        cursor.execute("DROP TABLE IF EXISTS vehicles_new")
        cursor.execute("""
        CREATE TABLE vehicles_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            type_id INTEGER NOT NULL,
            brand TEXT NOT NULL,
            model TEXT NOT NULL,
            plate TEXT NOT NULL,
            year INTEGER NOT NULL,
            mileage INTEGER NOT NULL DEFAULT 0,
            max_mileage INTEGER NOT NULL DEFAULT 50000,
            image_url TEXT,
            next_service TEXT DEFAULT 'Pending Service Config',
            is_favorite BOOLEAN DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (type_id) REFERENCES vehicle_types (id)
        )
        """)

        # 4. Copy data from old to new
        selectable_cols = [col for col in columns if col != 'type']
        cols_str = ", ".join(selectable_cols)
        cursor.execute(f"INSERT INTO vehicles_new ({cols_str}) SELECT {cols_str} FROM vehicles")

        # 5. Swap tables
        cursor.execute("DROP TABLE vehicles")
        cursor.execute("ALTER TABLE vehicles_new RENAME TO vehicles")

        # Re-create indexes
        cursor.execute("CREATE INDEX idx_vehicles_user_id ON vehicles(user_id)")
        cursor.execute("CREATE INDEX idx_vehicles_type_id ON vehicles(type_id)")
        cursor.execute("CREATE UNIQUE INDEX idx_vehicles_plate ON vehicles(plate)")

        conn.commit()
        print("Migration successful! Obsolete 'type' column removed.")

    except Exception as e:
        conn.rollback()
        print(f"Error during migration: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    fix_schema()
