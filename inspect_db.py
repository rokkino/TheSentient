import sqlite3
import os

DB_PATH = "data/databases/thesentient.db"

def inspect_decisions():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get table info
    cursor.execute("PRAGMA table_info(decisions)")
    cols = cursor.fetchall()
    print("Columns in decisions table:")
    for col in cols:
        print(f"  {col}")
    
    # Get sample data
    cursor.execute("SELECT * FROM decisions LIMIT 5")
    rows = cursor.fetchall()
    print(f"\nSample rows ({len(rows)}):")
    for row in rows:
        print(row)
    
    conn.close()

if __name__ == "__main__":
    inspect_decisions()