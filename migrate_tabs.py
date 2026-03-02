import sqlite3
import json

db_path = "c:/Users/gianluca.rocca/OneDrive - alpitronic GmbH/Documents/vscode/TheSentient/thesentient.db"

def migrate_tabs():
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, username, tabs FROM users")
        users = cursor.fetchall()
        
        updates = 0
        for row in users:
            uid, uname, tabs_json = row
            if tabs_json:
                try:
                    tabs = json.loads(tabs_json)
                    changed = False
                    for tab in tabs:
                        if tab.get("name") in ["GRaPH", "Stocks"]:
                            tab["name"] = "CHARTS"
                            changed = True
                    if changed:
                        new_json = json.dumps(tabs)
                        cursor.execute("UPDATE users SET tabs = ? WHERE id = ?", (new_json, uid))
                        updates += 1
                        print(f"Updated tabs for user {uname} ({uid})")
                except json.JSONDecodeError:
                    print(f"Failed to parse tabs for user {uname}")
                    
        conn.commit()
        conn.close()
        print(f"Migration complete! Updated {updates} users.")
    except Exception as e:
        print("Error during migration:", e)

if __name__ == "__main__":
    migrate_tabs()
