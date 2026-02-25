import requests
import json

def test():
    print("=== REGISTER ===")
    r = requests.post("http://localhost:8001/api/auth/register", json={
        "username": "newuser8",
        "email": "newuser8@example.com",
        "password": "password123"
    })
    print(r.status_code)
    try:
        print(json.dumps(r.json(), indent=2))
    except:
        print(r.text)

    print("\n=== LOGIN ===")
    r = requests.post("http://localhost:8001/api/auth/login", json={
        "username": "newuser8",
        "password": "password123"
    })
    print(r.status_code)
    try:
        print(json.dumps(r.json(), indent=2))
    except:
        print(r.text)

if __name__ == "__main__":
    test()
