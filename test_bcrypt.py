import sys
import os

BACKEND_DIR = os.path.join(os.getcwd(), "src", "backend", "backend")
sys.path.insert(0, BACKEND_DIR)

from services.auth_service import get_password_hash, verify_password

def test_hashing():
    pwd = "password123"
    hashed = get_password_hash(pwd)
    print(f"Hashed: {hashed}")
    print(f"Type of hashed: {type(hashed)}")
    
    is_valid = verify_password(pwd, hashed)
    print(f"Is valid: {is_valid}")
    
    is_invalid = verify_password("wrong", hashed)
    print(f"Is invalid (wrong pwd rejected): {not is_invalid}")

if __name__ == "__main__":
    test_hashing()
