import sqlite3
import os

db_path = r'f:\Labs\python\DriverTrack\drivetrack.db'

def deduplicate():
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM vehicle_types")
        rows = cursor.fetchall()
        print(f"Current vehicle types: {rows}")

        # Map labels to their first ID to find duplicates
        label_map = {}
        to_delete = []
        
        for row in rows:
            tid, slug, label, icon, image = row
            if label in label_map:
                print(f"Duplicate found for label '{label}': ID {tid} (slug: {slug})")
                to_delete.append((tid, label_map[label]))
            else:
                label_map[label] = tid

        for del_id, keep_id in to_delete:
            print(f"Moving vehicles from type {del_id} to {keep_id}...")
            cursor.execute("UPDATE vehicles SET type_id = ? WHERE type_id = ?", (keep_id, del_id))
            print(f"Deleting duplicate type {del_id}...")
            cursor.execute("DELETE FROM vehicle_types WHERE id = ?", (del_id,))

        conn.commit()
        print("Deduplication complete.")

    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    deduplicate()
