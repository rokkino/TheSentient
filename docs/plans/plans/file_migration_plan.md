# File Migration Plan for Minimal Root Structure

## Overview
This plan details the step-by-step migration of files from the cluttered root directory to the organized subdirectory structure.

## Current Root Inventory (Files to Move)

### Category 1: Python Scripts (35 files)
```
check_bot_api.py           → scripts/check/bot_api.py
check_bot_config.py        → scripts/check/bot_config.py
check_bots.py              → scripts/check/bots.py
check_earnings.py          → scripts/check/earnings.py
check_syntax.py            → scripts/check/syntax.py
debug_alpaca_conn.py       → scripts/debug/alpaca_conn.py
debug_bot.py               → scripts/debug/bot.py
list_bots.py               → scripts/list/bots.py
list_models.py             → scripts/list/models.py
reactivate_bot.py          → scripts/management/reactivate_bot.py
read_output.py             → scripts/utilities/read_output.py
reset_and_trigger.py       → scripts/management/reset_and_trigger.py
test_activate_bot.py       → scripts/test/activate_bot.py
test_bot_api.py            → scripts/test/bot_api.py
test_bot_orders.py         → scripts/test/bot_orders.py
test_bot_status.py         → scripts/test/bot_status.py
test_earnings_bot.py       → scripts/test/earnings_bot.py
test_gemini_models.py      → scripts/test/gemini_models.py
test_liquidation.py        → scripts/test/liquidation.py
test_market_data.py        → scripts/test/market_data.py
test_order_execution.py    → scripts/test/order_execution.py
test_process_earnings.py   → scripts/test/process_earnings.py
test_scheduler_logic.py    → scripts/test/scheduler_logic.py
test_sizing.py             → scripts/test/sizing.py
test_symbol_mapper.py      → scripts/test/symbol_mapper.py
verify_alpaca_env.py       → scripts/verify/alpaca_env.py
verify_alpaca_execution.py → scripts/verify/alpaca_execution.py
verify_backend.py          → scripts/verify/backend.py
verify_env.py              → scripts/verify/env.py
drop_decisions_table.py    → scripts/db/drop_decisions_table.py
fix_decisions_table.py     → scripts/db/fix_decisions_table.py
inspect_hex.py             → scripts/db/inspect_hex.py
```

### Category 2: Log/Output Files (10 files)
```
bot_debug_output.txt       → data/logs/bot_debug_output.txt
bot_status.txt             → data/logs/bot_status.txt
test_output_full.txt       → data/logs/test_output_full.txt
test_output.txt            → data/logs/test_output.txt
verify_error.log           → data/logs/verify_error.log
verify_log.txt             → data/logs/verify_log.txt
verify_output_root.log     → data/logs/verify_output_root.log
verify_output_testdb.log   → data/logs/verify_output_testdb.log
verify_output.txt          → data/logs/verify_output.txt
verify_sizing.txt          → data/logs/verify_sizing.txt
```

### Category 3: Database Files (2 files)
```
thesentient.db             → data/databases/thesentient.db
test_verify.db             → data/databases/test_verify.db
```

### Category 4: Configuration Files (1 file)
```
models.txt                 → config/models.txt
```

### Category 5: Batch/Script Files (3 files)
```
restart-backend.bat        → scripts/restart-backend.bat
start-dev.bat              → scripts/start-dev.bat
start-dev.sh               → scripts/start-dev.sh
```

### Category 6: Existing Directories (to be reorganized)
```
backend/                   → src/backend/ (move entire directory)
frontend/                  → src/frontend/ (move entire directory)
legacy_bot/                → src/legacy_bot/ (move entire directory)
streamlit_app/             → src/streamlit_app/ (move entire directory)
assets/                    → src/assets/ (move entire directory)
plans/                     → docs/plans/ (move entire directory)
scripts/                   → scripts/ (reorganize contents)
modular/                   → src/modular/ (move entire directory)
```

## Migration Sequence

### Step 1: Backup
```bash
# Create timestamped backup
BACKUP_DIR="../TheSentient_backup_$(date +%Y%m%d_%H%M%S)"
cp -r . "$BACKUP_DIR"
git add .
git commit -m "Pre-migration backup"
```

### Step 2: Create Target Directory Structure
```bash
# Create main directories
mkdir -p src/backend src/frontend src/legacy_bot src/streamlit_app src/assets src/modular
mkdir -p data/databases data/logs data/uploads data/cache
mkdir -p config/environment
mkdir -p docs/plans docs/api docs/architecture

# Create scripts subdirectories
mkdir -p scripts/check scripts/debug scripts/list scripts/management
mkdir -p scripts/test scripts/verify scripts/db scripts/utilities

# Add __init__.py files for Python packages
find scripts -type d -exec touch {}/__init__.py \;
```

### Step 3: Move Existing Directories
```bash
# Move existing directories to src/
mv backend/ src/backend/
mv frontend/ src/frontend/
mv legacy_bot/ src/legacy_bot/
mv streamlit_app/ src/streamlit_app/
mv assets/ src/assets/
mv modular/ src/modular/

# Move plans to docs/
mv plans/ docs/plans/
```

### Step 4: Move Individual Files
```bash
# Move Python scripts
for file in check_*.py; do mv "$file" scripts/check/; done
mv debug_*.py scripts/debug/
mv list_*.py scripts/list/
mv reactivate_bot.py reset_and_trigger.py scripts/management/
mv read_output.py scripts/utilities/
for file in test_*.py; do mv "$file" scripts/test/; done
for file in verify_*.py; do mv "$file" scripts/verify/; done
mv drop_decisions_table.py fix_decisions_table.py inspect_hex.py scripts/db/

# Move log files
mv *.txt *.log data/logs/ 2>/dev/null || true
# Keep specific log files in root if needed
mv data/logs/README.md .  # If README was accidentally moved

# Move database files
mv *.db data/databases/ 2>/dev/null || true

# Move configuration
mv models.txt config/

# Move batch scripts
mv *.bat *.sh scripts/ 2>/dev/null || true
```

### Step 5: Reorganize Existing scripts/ Directory
```bash
# Move existing scripts to appropriate subdirectories
cd scripts

# Categorize existing scripts
mv verify_*.py check/ 2>/dev/null || true
mv debug_import.py debug/
mv inspect_*.py db/
mv delete_bot.py ota_update.py management/
mv test_*.py test/
mv get_earnings_*.py utilities/

cd ..
```

### Step 6: Create Root main.py
```python
# Create the new main.py in root
cat > main.py << 'EOF'
#!/usr/bin/env python3
"""
The Sentient - Modular Trading System
Primary entry point for the modular architecture.
"""

import os
import sys
from pathlib import Path

def main():
    """Main entry point - redirects to appropriate system"""
    print("The Sentient Trading System")
    print("============================")
    print()
    print("Available systems:")
    print("1. Modular System (new) - src/modular/")
    print("2. Legacy Backend - src/backend/")
    print("3. Legacy Bot - src/legacy_bot/")
    print("4. Streamlit App - src/streamlit_app/")
    print()
    print("To run a specific system, navigate to its directory:")
    print("  cd src/backend && python -m uvicorn main:app --reload")
    print("  cd src/legacy_bot && python main.py")
    print("  cd src/streamlit_app && streamlit run app.py")
    print()
    print("Or use the provided scripts:")
    print("  python scripts/start-dev.bat")
    print("  ./scripts/start-dev.sh")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
EOF
```

### Step 7: Update Path References
Create a path update script:
```python
# scripts/update_paths.py
import os
import re
from pathlib import Path

def update_file_paths(file_path):
    """Update hardcoded paths in a Python file"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Replace common path patterns
    replacements = [
        (r'"backend/thesentient\.db"', '"../data/databases/thesentient.db"'),
        (r"os\.path\.join\('backend', 'thesentient\.db'\)", 
         "os.path.join('..', 'data', 'databases', 'thesentient.db')"),
        (r'"\./thesentient\.db"', '"../data/databases/thesentient.db"'),
        # Add more patterns as needed
    ]
    
    updated = content
    for pattern, replacement in replacements:
        updated = re.sub(pattern, replacement, updated)
    
    if updated != content:
        with open(file_path, 'w') as f:
            f.write(updated)
        print(f"Updated: {file_path}")

# Run on all Python files
for root, dirs, files in os.walk('.'):
    for file in files:
        if file.endswith('.py'):
            update_file_paths(os.path.join(root, file))
```

### Step 8: Create Convenience Scripts
```bash
# Create run-modular.sh
cat > scripts/run-modular.sh << 'EOF'
#!/bin/bash
cd src/modular
python -m uvicorn modular.api.router:app --reload --host 127.0.0.1 --port 8000
EOF
chmod +x scripts/run-modular.sh

# Create run-backend.sh
cat > scripts/run-backend.sh << 'EOF'
#!/bin/bash
cd src/backend
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
EOF
chmod +x scripts/run-backend.sh
```

### Step 9: Update Documentation
```bash
# Update README.md
cat >> README.md << 'EOF'

## New Directory Structure

After reorganization, the project has the following structure:

```
TheSentient/
├── main.py                    # Primary entry point
├── README.md                  # This file
├── .gitignore                # Git ignore rules
├── .env.example              # Environment template
├── docker-compose.yml        # Docker orchestration
├── src/                      # Source code
│   ├── modular/             # New modular system
│   ├── backend/             # FastAPI backend
│   ├── frontend/            # Vue.js frontend
│   ├── legacy_bot/          # Legacy trading bot
│   └── streamlit_app/       # Streamlit application
├── scripts/                  # Utility scripts
├── config/                  # Configuration files
├── data/                    # Data and logs
└── docs/                    # Documentation
```

## Running the System

### Modular System (New)
```bash
./scripts/run-modular.sh
```

### Legacy Backend
```bash
./scripts/run-backend.sh
```

### Development
```bash
./scripts/start-dev.sh
```
EOF
```

### Step 10: Test Migration
```bash
# Test database connections
python -c "import sqlite3; conn = sqlite3.connect('data/databases/thesentient.db'); print('Database OK')"

# Test script imports
python -c "import sys; sys.path.insert(0, 'scripts/check'); import bot_api; print('Script imports OK')"

# Test backend
cd src/backend && python -c "import main; print('Backend imports OK')" && cd ../..

# Test modular system
cd src/modular && python -c "import sys; print('Modular system OK')" && cd ../..
```

## Rollback Plan

If migration fails:
```bash
# Restore from backup
rm -rf *
cp -r "$BACKUP_DIR"/* .
# Or use git
git reset --hard HEAD
git clean -fd
```

## Verification Checklist

- [ ] All Python files moved from root
- [ ] All log files moved to data/logs/
- [ ] Database files moved to data/databases/
- [ ] Configuration moved to config/
- [ ] Existing directories moved to src/
- [ ] Scripts reorganized into categories
- [ ] Root main.py created
- [ ] Path references updated
- [ ] Convenience scripts created
- [ ] Documentation updated
- [ ] All tests pass
- [ ] Git commit created

## Post-Migration Tasks

1. **Update Dockerfile** to reflect new paths
2. **Update CI/CD pipelines** for new structure
3. **Update IDE configurations** (VS Code, PyCharm)
4. **Communicate changes** to team members
5. **Monitor for path-related issues** in logs

## Expected Outcome

After migration, the root directory will contain only:
- `main.py`
- `README.md`
- Configuration files (`.gitignore`, `.env.example`, `docker-compose.yml`)
- Key directories (`src/`, `scripts/`, `config/`, `data/`, `docs/`)

This creates the "comfy to use folder" with a clean, organized structure that's easy for both humans and AI agents to navigate.