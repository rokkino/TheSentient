from src.backend.models.user import init_db, SessionLocal, engine
from sqlalchemy import text

def drop_decisions_table():
    print("Dropping decisions table...")
    try:
        with engine.connect() as connection:
            connection.execute(text("DROP TABLE IF EXISTS decisions"))
        print("Table dropped successfully.")
        
        print("Recreating tables...")
        init_db()
        print("Tables recreated.")
        
    except Exception as e:
        print(f"Error dropping table: {e}")

if __name__ == "__main__":
    drop_decisions_table()
