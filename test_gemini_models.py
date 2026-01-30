"""
Test Gemini API with different model configurations
"""
import google.generativeai as genai
import os
import sqlite3
import json

# Get key from DB
api_key = os.getenv('GOOGLE_GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
if not api_key:
    try:
        db_path = os.path.join("backend", "thesentient.db")
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

print(f"API Key found: {api_key[:10]}...")

genai.configure(api_key=api_key)

# Test different models
models_to_test = [
    'gemini-3.0-flash',
    'gemini-3-pro-preview',
    'gemini-3-flash-preview'
]

print("\nTesting models...\n")

for model_name in models_to_test:
    try:
        print(f"Testing {model_name}...")
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Say 'OK' if you can read this.")
        print(f"  ✅ SUCCESS: {response.text[:50]}")
        break  # Use first working model
    except Exception as e:
        error_msg = str(e)
        if "404" in error_msg:
            print(f"  ❌ Model not found")
        elif "429" in error_msg:
            print(f"  ❌ Rate limit")
        elif "403" in error_msg:
            print(f"  ❌ Permission denied")
        else:
            print(f"  ❌ Error: {error_msg[:100]}")

print("\n\nListing all available models:")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"  - {m.name}")
except Exception as e:
    print(f"Error listing models: {e}")
