import sys
import os

# Add the current directory to sys.path so we can import backend
sys.path.append(os.getcwd())

print("Attempting to import src.backend.main...")
try:
    from backend import main
    print("Successfully imported backend.main")
except ImportError as e:
    print(f"ImportError: {e}")
except SyntaxError as e:
    print(f"SyntaxError: {e}")
except Exception as e:
    print(f"An error occurred: {e}")
