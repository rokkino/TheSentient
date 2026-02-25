import sqlite3
import os

# Database path
DB_PATH = os.path.join("backend", "../data/databases/thesentient.db")

def delete_bot(bot_id):
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        print(f"Deleting bot with ID {bot_id}...")
        cursor.execute("DELETE FROM bots WHERE id = ?", (bot_id,))
        conn.commit()
        
        if cursor.rowcount > 0:
            print(f"Successfully deleted bot with ID {bot_id}")
        else:
            print(f"No bot found with ID {bot_id}")
            
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    delete_bot(2)
