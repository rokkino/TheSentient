import sqlite3
import os

DB_PATH = os.path.join(os.getcwd(), "src", "backend", "backend", "thesentient.db")

def check_db():
    if not os.path.exists(DB_PATH):
        print(f"DB not found at {DB_PATH}")
        return
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT id, username, email, hashed_password, is_active FROM users ORDER BY id DESC LIMIT 5")
        rows = cursor.fetchall()
        print("Last 5 users:")
        for row in rows:
            print(f"ID: {row[0]}, Username: {row[1]}, Active: {row[4]}")
            print(f"  Hash: {row[3]}")
    except Exception as e:
        print(f"Error querying users: {e}")
        
    conn.close()

if __name__ == "__main__":
    check_db()
