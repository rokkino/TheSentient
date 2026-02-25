
import os
import sys

# Test database path
db_path = os.path.join('..', 'data', 'databases', 'thesentient.db')
print(f"Database path: {db_path}")
print(f"Exists: {os.path.exists(db_path)}")

# Test imports
try:
    import scripts.check.check_bot_api
    print("✓ scripts.check.check_bot_api imports successfully")
except ImportError as e:
    print(f"✗ scripts.check.check_bot_api import failed: {e}")

try:
    import src.backend.main
    print("✓ src.backend.main imports successfully")
except ImportError as e:
    print(f"✗ src.backend.main import failed: {e}")
