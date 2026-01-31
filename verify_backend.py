import requests
import json
import sys

BASE_URL = "http://localhost:8000/api"

def run_test():
    print(f"Testing connectivity to {BASE_URL}...")
    
    # 1. Check Health/Time (Basic server check)
    try:
        r = requests.get(f"{BASE_URL}/time", timeout=5)
        if r.status_code == 200:
            print("✅ Backend is UP (Time endpoint works)")
        else:
            print(f"❌ Backend returned {r.status_code} for /time")
            return
    except Exception as e:
        print(f"❌ Could not connect to backend: {e}")
        print("Please ensure the backend server is running (python main.py)")
        return

    # 2. Fetch Accounts
    account_id = None
    try:
        print("\nFetching accounts...")
        # Need a token? The backend might require auth. 
        # For simplicity, we'll try without, or we'd need to login. 
        # main.py dependency `get_current_user` is on these routes.
        # We need to simulate a login first.
        
        # Register/Login a dummy user or use existing? 
        # Let's try to just hit the execute endpoint with a dummy token if we can't login easily.
        # Actually, let's look at `test_bot_connection`. It requires `current_user`.
        # We need a valid token.
        
        # Attempt login with default creds if possible or user's creds?
        # User is "Gian". We don't have password.
        # We can bypass auth if we run this as a script importing the app? No, simpler to request.
        # Wait, I have direct DB access via python script.
        pass
    except Exception as e:
        print(f"Error: {e}")

    # DIRECT DB TEST (Bypasses API Auth issues for quick verification)
    # 3. Test Execute Route Existence
    print("\nTesting Execute Route (POST /api/bot/decisions/0/execute)...")
    try:
        # We expect 404, but we want to check the DETAIL
        r = requests.post(f"{BASE_URL}/bot/decisions/0/execute", timeout=5)
        print(f"Status: {r.status_code}")
        try:
            data = r.json()
            print(f"Body: {data}")
            
            if r.status_code == 404 and data.get("detail") == "Decision not found":
                print("✅ DIAGNOSIS: The route EXISTS and is working (Backend is updated).")
                print("The error 'Not Found' in frontend likely refers to the Decision ID/URL being invalid.")
            elif r.status_code == 404:
                 print("❌ DIAGNOSIS: The route returns generic 404.")
                 print("This confirms the BACKEND IS STALE and needs a restart.")
            elif r.status_code == 401:
                print("ℹ️ Route exists but requires Auth (Good sign).")
            else:
                print(f"ℹ️ Received unexpected status: {r.status_code}")
                
        except json.JSONDecodeError:
            print(f"Body (Text): {r.text}")
            
    except Exception as e:
        print(f"Request failed: {e}")


    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("Run this script from the project root.")
    except Exception as e:
        print(f"❌ Code Error: {e}")

if __name__ == "__main__":
    run_test()
