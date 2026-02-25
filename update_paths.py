#!/usr/bin/env python3
"""
Script to update import paths after file reorganization.
"""

import os
import re
from pathlib import Path

def update_file_paths(file_path):
    """Update hardcoded paths in a Python file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace common path patterns
    replacements = [
        # Database paths
        (r'"backend/thesentient\.db"', '"../data/databases/thesentient.db"'),
        (r'"backend\\thesentient\.db"', '"../data/databases/thesentient.db"'),
        (r"os\.path\.join\('backend', 'thesentient\.db'\)", 
         "os.path.join('..', 'data', 'databases', 'thesentient.db')"),
        (r"os\.path\.join\('\.\.', 'backend', 'thesentient\.db'\)",
         "os.path.join('..', 'data', 'databases', 'thesentient.db')"),
        (r'"\./thesentient\.db"', '"../data/databases/thesentient.db"'),
        (r'"thesentient\.db"', '"../data/databases/thesentient.db"'),
        
        # Import paths for moved modules
        (r'from backend\.', 'from src.backend.'),
        (r'import backend\.', 'import src.backend.'),
        (r'from services\.', 'from src.backend.services.'),
        (r'import services\.', 'import src.backend.services.'),
        (r'from models\.', 'from src.backend.models.'),
        (r'import models\.', 'import src.backend.models.'),
        
        # Script imports
        (r'from scripts.check.', 'from scripts.check.'),
        (r'import scripts.check.', 'import scripts.check.'),
        (r'from scripts.debug.', 'from scripts.debug.'),
        (r'import scripts.debug.', 'import scripts.debug.'),
        (r'from scripts.test.', 'from scripts.test.'),
        (r'import scripts.test.', 'import scripts.test.'),
        (r'from scripts.verify.', 'from scripts.verify.'),
        (r'import scripts.verify.', 'import scripts.verify.'),
    ]
    
    updated = content
    for pattern, replacement in replacements:
        updated = re.sub(pattern, replacement, updated)
    
    if updated != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(updated)
        print(f"Updated: {file_path}")
        return True
    return False

def main():
    """Update paths in all Python files"""
    updated_count = 0
    
    # Update scripts directory
    for root, dirs, files in os.walk('scripts'):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                if update_file_paths(file_path):
                    updated_count += 1
    
    # Update src directory
    for root, dirs, files in os.walk('src'):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                if update_file_paths(file_path):
                    updated_count += 1
    
    # Update root Python files
    for file in os.listdir('.'):
        if file.endswith('.py'):
            file_path = os.path.join('.', file)
            if update_file_paths(file_path):
                updated_count += 1
    
    print(f"\nUpdated {updated_count} files")
    
    # Create a simple test to verify paths
    print("\nCreating test script...")
    test_script = """
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
"""
    
    with open('test_paths.py', 'w', encoding='utf-8') as f:
        f.write(test_script)
    
    print("\nRun 'python test_paths.py' to verify paths")

if __name__ == "__main__":
    main()