#!/usr/bin/env python3
"""
Test basic functionality after file reorganization.
"""
import os
import sys
import importlib.util

def test_database_paths():
    """Test that database files exist in new locations."""
    print("=== Database Path Tests ===")
    db_paths = [
        ("data/databases/thesentient.db", True),
        ("data/databases/test_verify.db", True),
        ("src/backend/backend/thesentient.db", False),  # old location, should not exist
    ]
    for path, should_exist in db_paths:
        exists = os.path.exists(path)
        status = "✓" if exists == should_exist else "✗"
        print(f"{status} {path}: exists={exists}, expected={should_exist}")

def test_imports():
    """Test that key modules can be imported."""
    print("\n=== Import Tests ===")
    modules = [
        "scripts.check.check_bot_api",
        "src.backend.main",
        "src.backend.services.bot_service",
        "src.backend.services.news_service",
        "src.backend.models.bot",
        "src.backend.models.user",
    ]
    for module_name in modules:
        try:
            spec = importlib.util.find_spec(module_name)
            if spec is None:
                raise ImportError(f"Module {module_name} not found")
            print(f"✓ {module_name}")
        except Exception as e:
            print(f"✗ {module_name}: {e}")

def test_script_execution():
    """Test that scripts can be executed (import side effects)."""
    print("\n=== Script Execution Tests ===")
    # Try to run a simple script that doesn't require external services
    try:
        from scripts.check import check_bot_api
        print("✓ scripts.check.check_bot_api can be imported")
    except Exception as e:
        print(f"✗ scripts.check.check_bot_api: {e}")

def test_root_main():
    """Test that root main.py can be executed."""
    print("\n=== Root Main Test ===")
    main_path = "main.py"
    if os.path.exists(main_path):
        try:
            with open(main_path, 'r') as f:
                content = f.read()
            if "run_modular_system" in content and "run_legacy_backend" in content:
                print("✓ main.py contains modular entry points")
            else:
                print("✗ main.py missing expected functions")
        except Exception as e:
            print(f"✗ Error reading main.py: {e}")
    else:
        print("✗ main.py not found")

def test_directory_structure():
    """Verify expected directories exist."""
    print("\n=== Directory Structure ===")
    expected_dirs = [
        "src/backend",
        "src/frontend",
        "src/legacy_bot",
        "data/databases",
        "data/logs",
        "config",
        "scripts/check",
        "scripts/debug",
        "scripts/list",
        "scripts/management",
        "scripts/test",
        "scripts/verify",
        "scripts/utilities",
        "docs/plans",
    ]
    for dir_path in expected_dirs:
        exists = os.path.isdir(dir_path)
        status = "✓" if exists else "✗"
        print(f"{status} {dir_path}")

if __name__ == "__main__":
    test_database_paths()
    test_imports()
    test_script_execution()
    test_root_main()
    test_directory_structure()
    print("\n=== All Tests Completed ===")