import sqlite3
import os
import requests

# Check DB ownership
db_path = os.path.join("backend", "thesentient.db")
try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, email FROM users")
    users = cursor.fetchall()
    print("Users:")
    for u in users:
        print(f"  ID: {u[0]}, Email: {u[1]}")
        
    cursor.execute("SELECT id, name, user_id FROM bots")
    bots = cursor.fetchall()
    print("\nBots:")
    for b in bots:
        print(f"  ID: {b[0]}, Name: {b[1]}, User ID: {b[2]}")
        
    conn.close()
except Exception as e:
    print(f"DB Error: {e}")

# Check API
print("\nChecking API...")
try:
    response = requests.get("http://localhost:8000/bots")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"API Error: {e}")
