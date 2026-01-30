import requests
import sys
import time
from datetime import datetime

API_URL = "http://localhost:8000/api"

def test_time_endpoint():
    print("Testing /api/time endpoint...")
    try:
        response = requests.get(f"{API_URL}/time")
        if response.status_code == 200:
            data = response.json()
            print(f"SUCCESS: Server time: {data.get('server_time_formatted')}")
            print(f"ISO Time: {data.get('server_time_iso')}")
        else:
            print(f"FAILED: Status code {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"FAILED: Connection error: {e}")

if __name__ == "__main__":
    # Wait a bit for server reload if needed
    time.sleep(2)
    test_time_endpoint()
