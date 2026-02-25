# Cleanup Implementation Steps

## Overview
This document provides step-by-step instructions to clean up the root directory and organize files into a "comfy to use folder" structure.

## Phase 0: Preparation

### 0.1 Backup Current State
```bash
# Create backup of current root directory
cp -r . ../TheSentient_backup_$(date +%Y%m%d_%H%M%S)
```

### 0.2 Check Git Status
```bash
git status
git add .
git commit -m "Pre-cleanup backup"
```

## Phase 1: Create Directory Structure

### 1.1 Create New Directories
```bash
# Create main organization directories
mkdir -p config data logs

# Create scripts subdirectories
mkdir -p scripts/check scripts/debug scripts/list scripts/management
mkdir -p scripts/test scripts/verify scripts/db scripts/utilities

# Add __init__.py files to make Python packages
touch scripts/__init__.py
touch scripts/check/__init__.py scripts/debug/__init__.py scripts/list/__init__.py
touch scripts/management/__init__.py scripts/test/__init__.py scripts/verify/__init__.py
touch scripts/db/__init__.py scripts/utilities/__init__.py
```

## Phase 2: Move Files from Root Directory

### 2.1 Move Database Files
```bash
mv thesentient.db data/
mv test_verify.db data/
```

### 2.2 Move Log and Output Files
```bash
# Move all text/log files to logs directory
mv bot_debug_output.txt logs/
mv bot_status.txt logs/
mv test_output_full.txt logs/
mv test_output.txt logs/
mv verify_error.log logs/
mv verify_log.txt logs/
mv verify_output_root.log logs/
mv verify_output_testdb.log logs/
mv verify_output.txt logs/
mv verify_sizing.txt logs/
```

### 2.3 Move Configuration File
```bash
mv models.txt config/
```

### 2.4 Move Batch Scripts
```bash
mv restart-backend.bat scripts/
mv start-dev.bat scripts/
mv start-dev.sh scripts/
```

## Phase 3: Reorganize Python Scripts from Root

### 3.1 Move Check Scripts
```bash
mv check_bot_api.py scripts/check/
mv check_bot_config.py scripts/check/
mv check_bots.py scripts/check/
mv check_earnings.py scripts/check/
mv check_syntax.py scripts/check/
```

### 3.2 Move Debug Scripts
```bash
mv debug_alpaca_conn.py scripts/debug/
mv debug_bot.py scripts/debug/
```

### 3.3 Move List Scripts
```bash
mv list_bots.py scripts/list/
mv list_models.py scripts/list/
```

### 3.4 Move Management Scripts
```bash
mv reactivate_bot.py scripts/management/
mv reset_and_trigger.py scripts/management/
```

### 3.5 Move Test Scripts
```bash
mv test_activate_bot.py scripts/test/
mv test_bot_api.py scripts/test/
mv test_bot_orders.py scripts/test/
mv test_bot_status.py scripts/test/
mv test_earnings_bot.py scripts/test/
mv test_gemini_models.py scripts/test/
mv test_liquidation.py scripts/test/
mv test_market_data.py scripts/test/
mv test_order_execution.py scripts/test/
mv test_process_earnings.py scripts/test/
mv test_scheduler_logic.py scripts/test/
mv test_sizing.py scripts/test/
mv test_symbol_mapper.py scripts/test/
```

### 3.6 Move Verify Scripts
```bash
mv verify_alpaca_env.py scripts/verify/
mv verify_alpaca_execution.py scripts/verify/
mv verify_backend.py scripts/verify/
mv verify_env.py scripts/verify/
```

### 3.7 Move Database Scripts
```bash
mv drop_decisions_table.py scripts/db/
mv fix_decisions_table.py scripts/db/
mv inspect_hex.py scripts/db/
```

### 3.8 Move Utility Scripts
```bash
mv read_output.py scripts/utilities/
```

## Phase 4: Reorganize Existing scripts/ Directory

### 4.1 Categorize Existing Scripts
Current `scripts/` directory contains 25 files that need categorization:

#### Move to scripts/check/
```bash
mv scripts/verify_account_system.py scripts/check/
mv scripts/verify_changes.py scripts/check/
mv scripts/verify_gemini_models.py scripts/check/
mv scripts/verify_ig_connection.py scripts/check/
mv scripts/verify_time.py scripts/check/
```

#### Move to scripts/debug/
```bash
mv scripts/debug_import.py scripts/debug/
```

#### Move to scripts/db/
```bash
mv scripts/inspect_bots.py scripts/db/
mv scripts/inspect_gemini_models.py scripts/db/
mv scripts/inspect_ollama.py scripts/db/
```

#### Move to scripts/management/
```bash
mv scripts/delete_bot.py scripts/management/
mv scripts/ota_update.py scripts/management/
```

#### Move to scripts/test/
```bash
mv scripts/test_ai_draw.py scripts/test/
mv scripts/test_chat_search.py scripts/test/
mv scripts/test_financial_data.py scripts/test/
mv scripts/test_gemini_earnings.py scripts/test/
mv scripts/test_global.py scripts/test/
mv scripts/test_multi_indicator.py scripts/test/
mv scripts/test_name_error.py scripts/test/
mv scripts/test_news_caching.py scripts/test/
mv scripts/test_search_fallback.py scripts/test/
mv scripts/test_search_simulation.py scripts/test/
mv scripts/test_stockdex_data.py scripts/test/
mv scripts/test_yahoo_fin.py scripts/test/
mv scripts/test.py scripts/test/
```

#### Move to scripts/utilities/
```bash
mv scripts/get_earnings_by_date.py scripts/utilities/
mv scripts/get_earnings_stockdex.py scripts/utilities/
```

## Phase 5: Update File References

### 5.1 Update Database Paths
Many scripts reference `thesentient.db` or `backend/thesentient.db`. Need to update:

#### Common patterns to fix:
1. `"backend/thesentient.db"` → `"../data/thesentient.db"` (from scripts directory)
2. `os.path.join("backend", "thesentient.db")` → `os.path.join("..", "data", "thesentient.db")`
3. Hardcoded paths in Python files

### 5.2 Create Path Helper Function
Create `scripts/path_utils.py`:
```python
import os
from pathlib import Path

def get_project_root():
    """Return absolute path to project root"""
    return Path(__file__).resolve().parent.parent

def get_db_path():
    """Return path to main database"""
    return get_project_root() / "data" / "thesentient.db"

def get_backend_db_path():
    """Return path to database in backend directory (for compatibility)"""
    return get_project_root() / "backend" / "thesentient.db"
```

### 5.3 Update Critical Scripts
Update the most commonly used scripts first:
1. `scripts/check/bot_api.py`
2. `scripts/debug/bot.py`
3. `scripts/list/bots.py`
4. `scripts/management/reactivate_bot.py`

## Phase 6: Create Convenience Scripts

### 6.1 Create Root-Level Wrappers (Optional)
For backward compatibility, create simple wrapper scripts in root:

```python
# clean_root_wrapper.py example
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts', 'check'))
from bot_api import main
if __name__ == "__main__":
    main()
```

### 6.2 Create Main Entry Points
Create `scripts/run.py` with subcommands:
```python
# scripts/run.py
import argparse
import sys

def main():
    parser = argparse.ArgumentParser(description="The Sentient Script Runner")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Add subcommands for each script category
    # ...
    
    args = parser.parse_args()
    if args.command:
        # Dispatch to appropriate module
        pass
    else:
        parser.print_help()
        
if __name__ == "__main__":
    main()
```

## Phase 7: Verification and Testing

### 7.1 Test Script Execution
```bash
# Test each category
python scripts/check/bot_api.py
python scripts/debug/bot.py
python scripts/list/bots.py
python scripts/management/reactivate_bot.py
python scripts/test/activate_bot.py
python scripts/verify/env.py
python scripts/db/inspect_hex.py
```

### 7.2 Verify Database Connectivity
```bash
# Test database connections
python -c "import sqlite3; conn = sqlite3.connect('data/thesentient.db'); print('DB OK')"
```

### 7.3 Check Import Paths
```bash
# Test Python imports
python -c "import sys; sys.path.insert(0, 'scripts'); from check import bot_api; print('Imports OK')"
```

## Phase 8: Cleanup and Finalization

### 8.1 Remove Empty Directories
```bash
# Check for empty directories
find . -type d -empty
```

### 8.2 Update Documentation
Update `README.md` with new structure:
```markdown
## Project Structure

```
TheSentient/
├── README.md
├── config/           # Configuration files
├── data/            # Database files
├── logs/            # Log and output files
├── scripts/         # Utility scripts
│   ├── check/       # Verification scripts
│   ├── debug/       # Debugging tools
│   ├── list/        # Listing utilities
│   ├── management/  # System management
│   ├── test/        # Test scripts
│   ├── verify/      # Verification tools
│   ├── db/          # Database utilities
│   └── utilities/   # General utilities
├── backend/         # FastAPI backend
├── frontend/        # Vue.js frontend
├── legacy_bot/      # Legacy trading bot
├── modular/         # New modular system
├── plans/           # Documentation and plans
└── streamlit_app/   # Streamlit application
```

### 8.3 Update .gitignore
Add patterns for new directories:
```gitignore
# Logs
logs/*.log
logs/*.txt

# Data files (except sample/test)
data/*.db
!data/sample.db

# Temporary files
*.tmp
*.temp
```

### 8.4 Create Maintenance Script
Create `scripts/maintenance/organize.py` for future cleanup:
```python
"""
Maintenance script to keep directory organized
"""
import os
import shutil
from pathlib import Path

# Rules for auto-organizing new files
RULES = {
    'check_': 'check/',
    'debug_': 'debug/',
    'test_': 'test/',
    'verify_': 'verify/',
    # ...
}
```

## Expected Final Root Directory

After cleanup, root directory should contain:
```
.dockerignore
.env.example
.gitignore
docker-compose.yml
README.md
config/
data/
logs/
scripts/
backend/
frontend/
legacy_bot/
modular/
plans/
streamlit_app/
assets/
.github/
```

## Rollback Plan

If issues occur, revert using git:
```bash
git reset --hard HEAD  # Revert all changes
# Or restore from backup
cp -r ../TheSentient_backup/* .
```

## Success Criteria

1. **Root directory clean**: No Python files in root except maybe wrapper scripts
2. **All scripts functional**: Every moved script executes without errors
3. **Database accessible**: All database connections work with new paths
4. **Import paths valid**: Python imports work from new locations
5. **Documentation updated**: README reflects new structure

## Next Steps After Cleanup

1. **Implement modular system**: Proceed with modular architecture implementation
2. **Create unified CLI**: Develop comprehensive command-line interface
3. **Add automation**: Implement CI/CD for script testing
4. **Enforce organization**: Add pre-commit hooks to prevent clutter