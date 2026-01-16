import sqlite3
import os

DB_PATH = "backend/thesentient.db"

def update_schema():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    print(f"Updating database schema at {DB_PATH}...")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if column exists
        cursor.execute("PRAGMA table_info(bots)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'activity_data' in columns:
            print("Column 'activity_data' already exists in 'bots' table.")
        else:
            print("Adding 'activity_data' column to 'bots' table...")
            cursor.execute("ALTER TABLE bots ADD COLUMN activity_data TEXT")
            conn.commit()
            print("Column added successfully.")
            
        conn.close()
        print("Database schema update complete.")
        
    except Exception as e:
        print(f"Error updating database: {e}")

if __name__ == "__main__":
    update_schema()
