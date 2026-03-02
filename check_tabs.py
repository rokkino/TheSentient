import sqlite3
import json

db_path = "c:/Users/gianluca.rocca/OneDrive - alpitronic GmbH/Documents/vscode/TheSentient/thesentient.db"

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables:", tables)
    
    if ('users',) in tables:
        cursor.execute("PRAGMA table_info(users)")
        print("users schema:", cursor.fetchall())
        cursor.execute("SELECT id, username, tabs FROM users LIMIT 3;")
        for row in cursor.fetchall():
            print("User:", row[0], row[1])
            tabs = row[2]
            if tabs:
                print("Tabs:", tabs[:200]) # print first 200 chars
    conn.close()
except Exception as e:
    print("Error:", e)
