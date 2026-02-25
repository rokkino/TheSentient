import google.generativeai as genai
import os
import sqlite3
import json

# Get key from DB
api_key = os.getenv('GOOGLE_GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
if not api_key:
    try:
        db_path = os.path.join("backend", "../data/databases/thesentient.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT config FROM bots")
        bots = cursor.fetchall()
        for (config_json,) in bots:
            try:
                config = json.loads(config_json)
                if config.get('gemini_api_key'):
                    api_key = config.get('gemini_api_key')
                    break
            except:
                pass
        conn.close()
    except Exception as e:
        print(f"Error reading DB: {e}")

if not api_key:
    print("No API key found.")
    exit(1)

genai.configure(api_key=api_key)

print("Listing models...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
except Exception as e:
    print(f"Error listing models: {e}")
