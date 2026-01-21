import requests
import json
import os

# Base URL
BASE_URL = "http://localhost:8000/api"

def test_ask_gemini():
    print("Testing Ask Gemini Endpoint...")
    
    # Login first
    session = requests.Session()
    login_payload = {
        "username": "Gianluca",  # Assuming this user exists, otherwise we might need to register or use a known user
        "password": "password"   # Replace with actual password if known, or use a different approach
    }
    
    # Since we don't know the password, we can't easily automate this without a known test user.
    # However, for the purpose of this task, I'll try to use the 'admin' user if it exists or skip auth if I can't.
    # Actually, let's just use the frontend for verification as I don't want to guess passwords.
    # But wait, I can check if there is a way to get a token or just disable auth for testing? No, that's bad practice.
    
    # Let's try to register a temp user for testing
    import uuid
    temp_user = f"test_user_{str(uuid.uuid4())[:8]}"
    temp_pass = "testpass123"
    
    print(f"Registering temp user: {temp_user}")
    reg_response = requests.post(f"{BASE_URL}/auth/register", json={
        "username": temp_user,
        "email": f"{temp_user}@example.com",
        "password": temp_pass
    })
    
    if reg_response.status_code != 200:
        print(f"Registration failed: {reg_response.text}")
        # Try login anyway, maybe user exists
    
    print("Logging in...")
    login_response = requests.post(f"{BASE_URL}/auth/login", json={
        "username": temp_user,
        "password": temp_pass
    })
    
    if login_response.status_code != 200:
        print(f"Login failed: {login_response.text}")
        return

    token = login_response.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Payload for asking Gemini
    payload = {
        "symbol": "AAPL",
        "company": "Apple Inc.",
        "date": "2024-02-01",
        "question": "What are the revenue expectations?",
        "provider": "gemini"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/earnings/ask", json=payload, headers=headers)
        
        if response.status_code == 200:
            print("Success!")
            print("Response:", json.dumps(response.json(), indent=2))
        else:
            print(f"Failed with status {response.status_code}")
            print("Response:", response.text)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_ask_gemini()
