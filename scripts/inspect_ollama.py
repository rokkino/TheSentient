import requests
import json

base_url = "http://localhost:11434"

print(f"Checking Ollama at {base_url}...")

try:
    # Check tags (available models)
    response = requests.get(f"{base_url}/api/tags")
    if response.status_code == 200:
        models = response.json().get('models', [])
        print(f"\nAvailable Models ({len(models)}):")
        for m in models:
            print(f"- {m.get('name')} (Size: {m.get('size')})")
    else:
        print(f"Error checking tags: {response.status_code}")

    # Check running models (ps) - Note: /api/ps might not be available in all versions, but let's try
    response = requests.get(f"{base_url}/api/ps")
    if response.status_code == 200:
        running = response.json().get('models', [])
        print(f"\nRunning Models ({len(running)}):")
        for m in running:
            print(f"- {m.get('name')} (VRAM: {m.get('size_vram')})")
    else:
        print(f"\nCould not get running processes (might be older Ollama version): {response.status_code}")

except Exception as e:
    print(f"Error connecting to Ollama: {e}")
