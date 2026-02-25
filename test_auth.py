import requests

def test_auth():
    print("--- Testing Register ---")
    try:
        resp = requests.post("http://localhost:8001/api/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123"
        })
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.text}")
    except Exception as e:
        print(f"Error: {e}")

    print("\n--- Testing Login ---")
    try:
        resp = requests.post("http://localhost:8001/api/auth/login", data={
            "username": "testuser",
            "password": "password123"
        })
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_auth()
