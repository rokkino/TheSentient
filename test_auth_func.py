import sys
import os

BACKEND_DIR = os.path.join(os.getcwd(), "src", "backend", "backend")
sys.path.insert(0, BACKEND_DIR)

# Fix relative imports by changing directory
os.chdir(BACKEND_DIR)
import sqlite3
from sqlalchemy.orm import Session
from models.user import SessionLocal, get_db
from services.auth_service import authenticate_user

def test():
    db = SessionLocal()
    try:
        from models.user import engine
        import sqlite3
        import os
        print(f"SQLAlchemy URL: {engine.url}")
        print(f"Absolute path: {os.path.abspath('./thesentient.db')}")
        
        # Test raw connect here
        conn = sqlite3.connect('./thesentient.db')
        cur = conn.cursor()
        cur.execute("SELECT count(*) FROM users")
        print(f"Raw count in this cwd: {cur.fetchone()[0]}")
        
        print("All users via SQLAlchemy:")
        from models.user import User
        all_users = db.query(User).all()
        for u in all_users:
            print(f"- '{u.username}' (ID: {u.id})")
            
        print("Testing authenticate_user...")
        user = authenticate_user(db, "newuser8", "password123")
        if user:
            print(f"SUCCESS: {user.username}")
        else:
            print("FAILED")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test()
