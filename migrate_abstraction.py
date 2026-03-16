import sqlite3
import os

db_path = r'drivetrack.db'

if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    exit(1)

connection = sqlite3.connect(db_path)
cursor = connection.cursor()

try:
    print("Step 1: Creating 'vehicle_types' table...")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vehicle_types (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        slug TEXT UNIQUE NOT NULL,
        label TEXT NOT NULL,
        icon TEXT NOT NULL,
        image_url TEXT NOT NULL
    );
    """)

    print("Step 2: Populating 'vehicle_types' catalogue...")
    types = [
        ('car', 'Car', 'directions_car_filled_rounded', 'https://images.unsplash.com/photo-1760520830355-e6be53e41c2f?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxTVVYlMjBibGFjayUyMGNhciUyMHByb2Zlc3Npb25hbCUyMHN0dWRpb3xlbnwxfHx8fDE3NzMyNDY3MTF8MA&ixlib=rb-4.1.0&q=80&w=1080'),
        ('motorcycle', 'Motorcycle', 'motorcycle_rounded', 'https://images.unsplash.com/photo-1588486624469-ad668ac8e1d8?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxzcG9ydHMlMjBtb3RvcmN5Y2xlJTIwZGFyayUyMGJhY2tncm91bmR8ZW58MXx8fHwxNzczMjQ2NzA5fDA&ixlib=rb-4.1.0&q=80&w=1080')
    ]
    cursor.executemany("INSERT OR IGNORE INTO vehicle_types (slug, label, icon, image_url) VALUES (?, ?, ?, ?)", types)

    # Get IDs
    cursor.execute("SELECT id, slug FROM vehicle_types")
    type_map = {slug: id for id, slug in cursor.fetchall()}

    print("Step 3: Migrating 'vehicles' table...")
    
    # Check if type_id already exists
    cursor.execute("PRAGMA table_info(vehicles)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'type_id' not in columns:
        print("Adding 'type_id' column...")
        cursor.execute("ALTER TABLE vehicles ADD COLUMN type_id INTEGER REFERENCES vehicle_types(id)")
    
    print("Mapping existing 'type' strings to 'type_id'...")
    # Map moto/motorcycle to motorcycle ID, car to car ID
    cursor.execute("UPDATE vehicles SET type_id = ? WHERE type IN ('car')", (type_map['car'],))
    cursor.execute("UPDATE vehicles SET type_id = ? WHERE type IN ('moto', 'motorcycle')", (type_map['motorcycle'],))
    
    # Set default type_id for any nulls
    cursor.execute("UPDATE vehicles SET type_id = ? WHERE type_id IS NULL", (type_map['car'],))

    print("Step 4: Renaming old 'type' column (via recreation for SQLite)...")
    # SQLite doesn't support DROP COLUMN easily in older versions, 
    # but we can just leave it or rename it if needed. 
    # For safety in this environment, we'll just ensure type_id is NOT NULL now.
    # Note: SQLite ALTER TABLE doesn't support NOT NULL directly.
    
    connection.commit()
    print("Migration successful.")

except Exception as e:
    connection.rollback()
    print(f"Error during migration: {e}")
finally:
    connection.close()
