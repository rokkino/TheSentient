import sqlite3
import os

# Database path
DB_PATH = os.path.join("backend", "thesentient.db")
OUTPUT_FILE = "bot_info.txt"

def list_bots():
    if not os.path.exists(DB_PATH):
        with open(OUTPUT_FILE, "w") as f:
            f.write(f"Database not found at {DB_PATH}")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        with open(OUTPUT_FILE, "w") as f:
            f.write("--- Schema ---\n")
            cursor.execute("PRAGMA table_info(bots)")
            for col in cursor.fetchall():
                f.write(str(col) + "\n")
            f.write("--------------\n")

            f.write("--- Bots ---\n")
            cursor.execute("SELECT * FROM bots WHERE name='Earnings Report Genius'")
            bots = cursor.fetchall()
            
            for bot in bots:
                f.write(str(bot) + "\n")
            
        conn.close()
    except Exception as e:
        with open(OUTPUT_FILE, "w") as f:
            f.write(f"Error: {e}")

if __name__ == "__main__":
    list_bots()
