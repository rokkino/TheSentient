import sqlite3
import os
import json

db_path = os.path.join("backend", "../data/databases/thesentient.db")

if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
else:
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='bots'")
        if not cursor.fetchone():
            print("Table 'bots' does not exist.")
        else:
            cursor.execute("SELECT id, name, is_active, config FROM bots")
            bots = cursor.fetchall()
            
            print(f"Found {len(bots)} bots.")
            for bot in bots:
                print(f"ID: {bot[0]}, Name: {bot[1]}, Active: {bot[2]}")
                # print(f"Config: {bot[3]}")
                
        conn.close()
    except Exception as e:
        print(f"Error reading DB: {e}")
