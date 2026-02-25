#!/usr/bin/env python3
import sqlite3
import os

def check_db(path):
    if not os.path.exists(path):
        print(f"  DB not found: {path}")
        return False
    conn = sqlite3.connect(path)
    cursor = conn.cursor()
    try:
        cursor.execute("PRAGMA table_info(decisions)")
        columns = cursor.fetchall()
        col_names = [col[1] for col in columns]
        print(f"  Columns: {col_names}")
        conn.close()
        return col_names
    except Exception as e:
        print(f"  Error: {e}")
        conn.close()
        return []

paths = [
    ("src/backend/backend/thesentient.db", "Backend default"),
    ("data/databases/thesentient.db", "Data directory"),
]

for path, desc in paths:
    print(f"\n{desc}: {path}")
    check_db(path)

# Also check which database is being used by the app
print("\n--- Checking DATABASE_URL environment ---")
import sys
sys.path.insert(0, 'src/backend/backend')
try:
    from models.user import DATABASE_URL, engine
    print(f"DATABASE_URL: {DATABASE_URL}")
    print(f"Engine URL: {engine.url}")
except Exception as e:
    print(f"Could not import: {e}")