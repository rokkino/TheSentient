import sys
import os

print(f"Python Executable: {sys.executable}")
print(f"Python Version: {sys.version}")
print(f"CWD: {os.getcwd()}")

try:
    import trading_ig
    print(f"trading_ig imported successfully: {trading_ig.__file__}")
except ImportError as e:
    print(f"Error importing trading_ig: {e}")
except Exception as e:
    print(f"Unexpected error importing trading_ig: {e}")

try:
    from trading_ig import IGService
    print("IGService imported successfully")
except Exception as e:
    print(f"Error importing IGService: {e}")
