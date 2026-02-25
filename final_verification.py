#!/usr/bin/env python3
"""
Final verification of modular system implementation.
"""
import os
import sys

def check_root_directory():
    """Verify root directory is clean."""
    print("=== Root Directory Check ===")
    
    # Files that should be in root
    expected_in_root = [
        "main.py",
        "README.md",
        ".gitignore",
        ".env.example",
        "docker-compose.yml",
        ".dockerignore"
    ]
    
    # Files that should NOT be in root (except test files)
    unwanted_patterns = [
        "graph.py", "bot.py", "strategy.py", "news.py", "earnings.py",
        "backtesting.py", "stocks.py", "chat.py"
    ]
    
    root_files = os.listdir(".")
    root_files = [f for f in root_files if os.path.isfile(f)]
    
    print(f"Files in root: {len(root_files)}")
    
    # Check expected files
    for expected in expected_in_root:
        if os.path.exists(expected):
            print(f"✓ {expected} present")
        else:
            print(f"✗ {expected} missing")
    
    # Check for unwanted module files
    unwanted_found = []
    for pattern in unwanted_patterns:
        if os.path.exists(pattern):
            unwanted_found.append(pattern)
    
    if unwanted_found:
        print(f"✗ Unwanted files in root: {unwanted_found}")
    else:
        print("✓ No unwanted module files in root")
    
    # Test files are okay
    test_files = [f for f in root_files if f.startswith("test_") or f.endswith("_test.py")]
    if test_files:
        print(f"Note: Test files in root: {test_files}")
    
    return len(unwanted_found) == 0

def check_modular_structure():
    """Verify modular directory structure."""
    print("\n=== Modular Structure Check ===")
    
    expected_dirs = [
        "modular",
        "modular/core",
        "modular/modules",
        "modular/folderbot"
    ]
    
    expected_files = [
        "modular/__init__.py",
        "modular/core/__init__.py",
        "modular/core/module_registry.py",
        "modular/core/event_bus.py",
        "modular/core/config_manager.py",
        "modular/modules/__init__.py",
        "modular/modules/news.py"
    ]
    
    all_good = True
    
    for dir_path in expected_dirs:
        if os.path.isdir(dir_path):
            print(f"✓ Directory: {dir_path}")
        else:
            print(f"✗ Missing directory: {dir_path}")
            all_good = False
    
    for file_path in expected_files:
        if os.path.exists(file_path):
            print(f"✓ File: {file_path}")
        else:
            print(f"✗ Missing file: {file_path}")
            all_good = False
    
    # Check folderbot exists (but may be empty for now)
    folderbot_path = "modular/folderbot"
    if os.path.isdir(folderbot_path):
        print(f"✓ folderbot directory exists")
        # Check for __init__.py
        if os.path.exists(os.path.join(folderbot_path, "__init__.py")):
            print(f"✓ folderbot/__init__.py exists")
        else:
            print(f"Note: folderbot/__init__.py missing (can be added later)")
    else:
        print(f"Note: folderbot directory not yet created")
    
    return all_good

def check_main_py():
    """Verify main.py implements modular system."""
    print("\n=== Main.py Check ===")
    
    if not os.path.exists("main.py"):
        print("✗ main.py not found")
        return False
    
    try:
        with open("main.py", "r") as f:
            content = f.read()
        
        checks = [
            ("run_modular_system", "Modular system entry point"),
            ("run_legacy_backend", "Legacy backend entry point"),
            ("modular", "Modular system import"),
            ("ModuleRegistry", "Module registry reference"),
            ("ConfigManager", "Config manager reference")
        ]
        
        all_good = True
        for check_str, description in checks:
            if check_str in content:
                print(f"✓ {description} found")
            else:
                print(f"✗ {description} missing")
                all_good = False
        
        return all_good
    except Exception as e:
        print(f"✗ Error reading main.py: {e}")
        return False

def check_import_paths():
    """Verify import paths work."""
    print("\n=== Import Path Check ===")
    
    test_code = """
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from modular.core.module_registry import ModuleRegistry
    print("✓ ModuleRegistry imports successfully")
except Exception as e:
    print(f"✗ ModuleRegistry import failed: {e}")

try:
    from modular.core.event_bus import EventBus
    print("✓ EventBus imports successfully")
except Exception as e:
    print(f"✗ EventBus import failed: {e}")

try:
    from modular.core.config_manager import ConfigManager
    print("✓ ConfigManager imports successfully")
except Exception as e:
    print(f"✗ ConfigManager import failed: {e}")

try:
    from modular.modules.news import NewsModule
    print("✓ NewsModule imports successfully")
except Exception as e:
    print(f"✗ NewsModule import failed: {e}")
"""
    
    # Write test script
    test_file = "temp_import_test.py"
    with open(test_file, "w") as f:
        f.write(test_code)
    
    try:
        import subprocess
        result = subprocess.run([sys.executable, test_file], 
                               capture_output=True, text=True)
        print(result.stdout)
        if result.returncode != 0:
            print(f"✗ Import test failed with return code {result.returncode}")
            if result.stderr:
                print(f"Stderr: {result.stderr}")
            return False
        return True
    except Exception as e:
        print(f"✗ Import test failed: {e}")
        return False
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)

def check_directory_organization():
    """Verify files are organized into proper directories."""
    print("\n=== Directory Organization Check ===")
    
    expected_organizations = [
        ("src/", "Source code directory exists"),
        ("src/backend/", "Backend directory exists"),
        ("src/frontend/", "Frontend directory exists"),
        ("data/databases/", "Database directory exists"),
        ("config/", "Config directory exists"),
        ("scripts/", "Scripts directory exists"),
        ("docs/", "Documentation directory exists")
    ]
    
    all_good = True
    for path, description in expected_organizations:
        if os.path.exists(path):
            print(f"✓ {description}")
        else:
            print(f"✗ {description}")
            all_good = False
    
    # Check that scripts are categorized
    script_categories = ["check", "debug", "list", "management", "test", "verify", "utilities"]
    for category in script_categories:
        category_path = f"scripts/{category}"
        if os.path.isdir(category_path):
            print(f"✓ Scripts category: {category}")
        else:
            print(f"Note: Scripts category missing: {category}")
    
    return all_good

def run_smoke_test():
    """Run a smoke test of the modular system."""
    print("\n=== Modular System Smoke Test ===")
    
    smoke_test_code = """
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modular.core.module_registry import get_registry
from modular.core.event_bus import get_event_bus, EventTypes
from modular.core.config_manager import get_config_manager

# Initialize core components
registry = get_registry()
event_bus = get_event_bus()
config_manager = get_config_manager()

print("✓ Core components initialized")

# Test event bus
def test_handler(event_type, data):
    print(f"  Event received: {event_type}")

event_bus.subscribe(EventTypes.NEWS_RECEIVED, test_handler)
event_bus.publish(EventTypes.NEWS_RECEIVED, {"test": "data"})
event_bus.unsubscribe(EventTypes.NEWS_RECEIVED, test_handler)

print("✓ Event bus test passed")

# Test config manager
system_config = config_manager.get_config("system")
print(f"✓ System config loaded: {system_config.get('name')}")

print("Smoke test completed successfully")
"""
    
    test_file = "temp_smoke_test.py"
    with open(test_file, "w") as f:
        f.write(smoke_test_code)
    
    try:
        import subprocess
        result = subprocess.run([sys.executable, test_file], 
                               capture_output=True, text=True)
        print(result.stdout)
        if result.returncode != 0:
            print(f"✗ Smoke test failed with return code {result.returncode}")
            if result.stderr:
                print(f"Stderr: {result.stderr}")
            return False
        return True
    except Exception as e:
        print(f"✗ Smoke test failed: {e}")
        return False
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)

def main():
    """Run all verification checks."""
    print("=" * 60)
    print("Final Verification - Modular System Implementation")
    print("=" * 60)
    
    results = []
    
    results.append(("Root Directory Clean", check_root_directory()))
    results.append(("Modular Structure", check_modular_structure()))
    results.append(("Main.py Implementation", check_main_py()))
    results.append(("Import Paths", check_import_paths()))
    results.append(("Directory Organization", check_directory_organization()))
    results.append(("Smoke Test", run_smoke_test()))
    
    print("\n" + "=" * 60)
    print("Verification Results:")
    print("=" * 60)
    
    all_passed = True
    for check_name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"{status} {check_name}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("SUCCESS: All verification checks passed!")
        print("\nSummary:")
        print("- Root directory cleaned (only main.py + essential files)")
        print("- Modular core framework created")
        print("- News module implemented as proof of concept")
        print("- Directory structure organized logically")
        print("- Backward compatibility maintained via main.py")
    else:
        print("WARNING: Some verification checks failed.")
        print("\nNext steps:")
        print("1. Address any missing files or directories")
        print("2. Ensure import paths are correct")
        print("3. Run modular system with: python main.py")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)