#!/usr/bin/env python3
import sqlite3
from datetime import datetime

conn = sqlite3.connect('src/backend/backend/thesentient.db')
cursor = conn.cursor()
cursor.execute("""
    SELECT id, bot_id, symbol, decision, status, execution_time, created_at, reasoning 
    FROM decisions 
    WHERE status IN ('PENDING', 'EXECUTED')
    ORDER BY symbol, execution_time
""")
rows = cursor.fetchall()
print(f"Total PENDING/EXECUTED decisions: {len(rows)}")
print("Symbols with PENDING/EXECUTED decisions:")
symbols = {}
for r in rows:
    sym = r[2]
    symbols[sym] = symbols.get(sym, 0) + 1

for sym, count in sorted(symbols.items()):
    print(f"  {sym}: {count}")

# Show details for first 20
print("\nDetails:")
for r in rows[:20]:
    print(f"ID:{r[0]} Bot:{r[1]} {r[2]} {r[3]} status:{r[4]} exec:{r[5]} created:{r[6]}")

# Check for any decisions with execution_time in future
cursor.execute("""
    SELECT COUNT(*) FROM decisions 
    WHERE status='PENDING' AND execution_time > datetime('now')
""")
future = cursor.fetchone()[0]
print(f"\nPending decisions with future execution_time: {future}")

cursor.execute("""
    SELECT symbol, execution_time FROM decisions 
    WHERE status='PENDING' AND execution_time > datetime('now')
    ORDER BY execution_time
""")
for sym, exec_time in cursor.fetchall():
    print(f"  {sym}: {exec_time}")

conn.close()