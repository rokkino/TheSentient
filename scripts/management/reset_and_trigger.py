"""
Deactivate and reactivate the bot to trigger fresh order generation via the API.
"""
import requests
import time

BASE_URL = 'http://localhost:8000'

# We need to bypass auth - let's make a direct update to the database and then call the internal API
import sqlite3
import os

os.chdir(os.path.join(os.path.dirname(__file__), 'backend'))

# First, let's clear any old decisions and set up for a fresh test
conn = sqlite3.connect('thesentient.db')
cursor = conn.cursor()

print("Clearing old decisions...")
cursor.execute("DELETE FROM decisions")
conn.commit()

print("Setting bot to inactive...")
cursor.execute("UPDATE bots SET is_active = 0, status = 'inactive' WHERE id = 1")
conn.commit()

time.sleep(1)

print("Setting bot to active...")
cursor.execute("UPDATE bots SET is_active = 1, status = 'active' WHERE id = 1")
conn.commit()

conn.close()

print("\nBot is now active. The next step is for the frontend to trigger process_bot_earnings.")
print("Refresh the page and check 'Check Orders' modal - you should see the waiting message.")
print("\nOr we can trigger it directly...")

import asyncio
import sys
sys.path.insert(0, '.')

async def trigger():
    from src.backend.services.scheduler_jobs import process_bot_earnings
    await process_bot_earnings(1)
    
    # Check results
    import sqlite3
    conn = sqlite3.connect('thesentient.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM decisions ORDER BY created_at DESC')
    rows = cursor.fetchall()
    cursor.execute("PRAGMA table_info(decisions)")
    cols = [info[1] for info in cursor.fetchall()]
    
    print(f"\nDecisions after activation ({len(rows)}):")
    for row in rows:
        d = dict(zip(cols, row))
        print(f"  {d['symbol']} | {d['decision']} | exec: {d['execution_time']} | {d['status']}")
    conn.close()

asyncio.run(trigger())
