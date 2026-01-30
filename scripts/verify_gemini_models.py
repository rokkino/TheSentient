import os
import sys
import sqlite3
import json
from google import genai
from google.genai import types

# Add backend to path to import models if needed, but we'll read DB directly for simplicity
sys.path.append(os.path.join(os.getcwd(), 'backend'))

def get_api_key():
    # Try updated profile first
    try:
        conn = sqlite3.connect('backend/thesentient.db')
        cursor = conn.cursor()
        cursor.execute("SELECT gemini_api_key FROM users ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        if row and row[0]:
            print(f"Found API key in DB (User table): {row[0][:5]}...")
            return row[0]
            
        # Try legacy bot config
        cursor.execute("SELECT config FROM bots")
        rows = cursor.fetchall()
        for (config_json,) in rows:
            try:
                config = json.loads(config_json)
                if config.get('gemini_api_key'):
                    print(f"Found API key in DB (Bot config): {config.get('gemini_api_key')[:5]}...")
                    return config.get('gemini_api_key')
            except:
                pass
        conn.close()
    except Exception as e:
        print(f"Error reading DB: {e}")
    
    # Try env var
    key = os.getenv('GOOGLE_GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
    if key:
        print(f"Found API key in environment: {key[:5]}...")
        return key
    
    return None

def test_models(api_key):
    if not api_key:
        print("No API key found.")
        return

    print("\nTesting models with API v1...")
    try:
        client = genai.Client(api_key=api_key, http_options={'api_version': 'v1'})
        for m in client.models.list(config={'page_size': 100}):
            print(f"- {m.name}")
    except Exception as e:
        print(f"Error listing models with v1: {e}")

    print("\nTesting models with API v1beta...")
    try:
        client_beta = genai.Client(api_key=api_key, http_options={'api_version': 'v1beta'})
        for m in client_beta.models.list(config={'page_size': 100}):
             print(f"- {m.name}")
    except Exception as e:
        print(f"Error listing models with v1beta: {e}")

    print("\nTesting generation with gemini-3-flash-preview (v1)...")
    try:
        client = genai.Client(api_key=api_key, http_options={'api_version': 'v1'})
        response = client.models.generate_content(
            model='gemini-3-flash-preview',
            contents='Hello'
        )
        print(f"Success! Response: {response.text}")
    except Exception as e:
        print(f"Failed with v1: {e}")

    print("\nTesting generation with gemini-3-flash-preview (v1beta)...")
    try:
        client = genai.Client(api_key=api_key, http_options={'api_version': 'v1beta'})
        response = client.models.generate_content(
            model='gemini-3-flash-preview',
            contents='Hello'
        )
        print(f"Success! Response: {response.text}")
    except Exception as e:
         print(f"Failed with v1beta: {e}")

if __name__ == "__main__":
    key = get_api_key()
    test_models(key)
