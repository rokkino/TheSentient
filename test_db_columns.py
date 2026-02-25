#!/usr/bin/env python3
import sqlite3
import os
import sys

DB_PATH = "data/databases/thesentient.db"

def test_columns():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get decisions table columns
    cursor.execute("PRAGMA table_info(decisions)")
    columns = cursor.fetchall()
    print("Decisions table columns:")
    for col in columns:
        print(f"  {col[1]} ({col[2]}) nullable={col[3]}")
    
    # Check for stop_loss and take_profit
    col_names = [col[1] for col in columns]
    if 'stop_loss' in col_names:
        print("OK: stop_loss column exists")
    else:
        print("MISSING: stop_loss column missing")
    if 'take_profit' in col_names:
        print("OK: take_profit column exists")
    else:
        print("MISSING: take_profit column missing")
    
    # Check for allocated_amount (should exist)
    if 'allocated_amount' in col_names:
        print("OK: allocated_amount column exists")
    else:
        print("MISSING: allocated_amount column missing")
    
    conn.close()

if __name__ == "__main__":
    test_columns()