import sys
import os
from pathlib import Path

# Emulate backend path setup
BACKEND_DIR = os.path.join(os.getcwd(), "src", "backend", "backend")
sys.path.insert(0, BACKEND_DIR)

try:
    import sgmllib
    print(f"sgmllib file: {sgmllib.__file__}")
    print(f"sgmllib attributes: {dir(sgmllib)}")
    print(f"shorttagopen in sgmllib: {'shorttagopen' in dir(sgmllib)}")
except Exception as e:
    print(f"Error: {e}")
