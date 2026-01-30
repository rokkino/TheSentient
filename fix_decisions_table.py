"""
Script to fix the decisions table schema.
The table is missing the 'bot_id' column which is required for the bot to create orders.
This script will:
1. Back up any existing data
2. Drop the old table
3. Recreate it with the correct schema
"""
import sqlite3
import os
import json
from datetime import datetime

# Try both paths (from project root or backend directory)
DB_PATHS = [
    "backend/thesentient.db",
    "thesentient.db",
]

def find_db():
    for p in DB_PATHS:
        if os.path.exists(p):
            return p
    return None

def fix_decisions_table():
    db_path = find_db()
    if not db_path:
        print("Database not found!")
        return False
    
    print(f"Using database: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if decisions table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='decisions'")
        if not cursor.fetchone():
            print("Decisions table doesn't exist. Will create it.")
        else:
            # Check current schema
            cursor.execute("PRAGMA table_info(decisions)")
            columns = [info[1] for info in cursor.fetchall()]
            print(f"Current columns: {columns}")
            
            if 'bot_id' in columns:
                print("Table already has 'bot_id' column. No fix needed.")
                conn.close()
                return True
            
            # Back up existing data if any
            cursor.execute("SELECT * FROM decisions")
            existing_data = cursor.fetchall()
            if existing_data:
                print(f"Backing up {len(existing_data)} existing records...")
                backup_file = f"decisions_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                # Get column names for backup
                cursor.execute("PRAGMA table_info(decisions)")
                cols = [info[1] for info in cursor.fetchall()]
                backup_data = [dict(zip(cols, row)) for row in existing_data]
                with open(backup_file, 'w') as f:
                    json.dump(backup_data, f, indent=2, default=str)
                print(f"Backup saved to {backup_file}")
            
            # Drop old table
            print("Dropping old decisions table...")
            cursor.execute("DROP TABLE decisions")
        
        # Create new table with correct schema
        print("Creating decisions table with correct schema...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bot_id INTEGER NOT NULL,
                symbol VARCHAR(20),
                decision VARCHAR(20),
                execution_time DATETIME,
                status VARCHAR(20) DEFAULT 'PENDING',
                reasoning TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                executed_at DATETIME,
                FOREIGN KEY (bot_id) REFERENCES bots(id)
            )
        """)
        
        # Create index for faster lookups
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_decisions_bot_id ON decisions(bot_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_decisions_status ON decisions(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_decisions_symbol ON decisions(symbol)")
        
        conn.commit()
        
        # Verify
        cursor.execute("PRAGMA table_info(decisions)")
        columns = [info[1] for info in cursor.fetchall()]
        print(f"New columns: {columns}")
        
        if 'bot_id' in columns:
            print("SUCCESS: decisions table now has 'bot_id' column!")
        else:
            print("ERROR: Fix failed!")
            conn.close()
            return False
        
        conn.close()
        print("Database schema fix complete!")
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    fix_decisions_table()
