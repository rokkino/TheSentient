# Root Directory Cleanup and Organization Plan

## Current State Analysis

The root directory contains **35+ Python files**, **10+ log/txt files**, and **multiple configuration files** that create clutter and reduce usability. The goal is to create a "comfy to use folder" structure by organizing these files into appropriate directories.

## File Categorization

### 1. Utility Scripts (Move to `scripts/` or subdirectories)
These are Python scripts for checking, debugging, verifying, and testing various system components:

- `check_bot_api.py` → `scripts/check/bot_api.py`
- `check_bot_config.py` → `scripts/check/bot_config.py`
- `check_bots.py` → `scripts/check/bots.py`
- `check_earnings.py` → `scripts/check/earnings.py`
- `check_syntax.py` → `scripts/check/syntax.py`
- `debug_alpaca_conn.py` → `scripts/debug/alpaca_conn.py`
- `debug_bot.py` → `scripts/debug/bot.py`
- `list_bots.py` → `scripts/list/bots.py`
- `list_models.py` → `scripts/list/models.py`
- `reactivate_bot.py` → `scripts/management/reactivate_bot.py`
- `read_output.py` → `scripts/utilities/read_output.py`
- `reset_and_trigger.py` → `scripts/management/reset_and_trigger.py`
- `test_activate_bot.py` → `scripts/test/activate_bot.py`
- `test_bot_api.py` → `scripts/test/bot_api.py`
- `test_bot_orders.py` → `scripts/test/bot_orders.py`
- `test_bot_status.py` → `scripts/test/bot_status.py`
- `test_earnings_bot.py` → `scripts/test/earnings_bot.py`
- `test_gemini_models.py` → `scripts/test/gemini_models.py`
- `test_liquidation.py` → `scripts/test/liquidation.py`
- `test_market_data.py` → `scripts/test/market_data.py`
- `test_order_execution.py` → `scripts/test/order_execution.py`
- `test_process_earnings.py` → `scripts/test/process_earnings.py`
- `test_scheduler_logic.py` → `scripts/test/scheduler_logic.py`
- `test_sizing.py` → `scripts/test/sizing.py`
- `test_symbol_mapper.py` → `scripts/test/symbol_mapper.py`
- `verify_alpaca_env.py` → `scripts/verify/alpaca_env.py`
- `verify_alpaca_execution.py` → `scripts/verify/alpaca_execution.py`
- `verify_backend.py` → `scripts/verify/backend.py`
- `verify_env.py` → `scripts/verify/env.py`

### 2. Database/Table Management (Move to `scripts/db/`)
- `drop_decisions_table.py` → `scripts/db/drop_decisions_table.py`
- `fix_decisions_table.py` → `scripts/db/fix_decisions_table.py`
- `inspect_hex.py` → `scripts/db/inspect_hex.py`

### 3. Log and Output Files (Move to `logs/` directory)
- `bot_debug_output.txt` → `logs/bot_debug_output.txt`
- `bot_status.txt` → `logs/bot_status.txt`
- `test_output_full.txt` → `logs/test_output_full.txt`
- `test_output.txt` → `logs/test_output.txt`
- `verify_error.log` → `logs/verify_error.log`
- `verify_log.txt` → `logs/verify_log.txt`
- `verify_output_root.log` → `logs/verify_output_root.log`
- `verify_output_testdb.log` → `logs/verify_output_testdb.log`
- `verify_output.txt` → `logs/verify_output.txt`
- `verify_sizing.txt` → `logs/verify_sizing.txt`

### 4. Configuration Files (Keep in root or move to `config/`)
- `.env.example` → Keep in root (standard practice)
- `.gitignore` → Keep in root (standard practice)
- `.dockerignore` → Keep in root (standard practice)
- `docker-compose.yml` → Keep in root (standard practice)
- `models.txt` → Move to `config/models.txt`

### 5. Database Files (Move to `data/` directory)
- `thesentient.db` → `data/thesentient.db`
- `test_verify.db` → `data/test_verify.db`

### 6. Batch/Script Files (Organize in `scripts/` or `bin/`)
- `restart-backend.bat` → `scripts/restart-backend.bat`
- `start-dev.bat` → `scripts/start-dev.bat`
- `start-dev.sh` → `scripts/start-dev.sh`

### 7. Documentation (Keep in root)
- `README.md` → Keep in root

## Proposed Directory Structure

```
TheSentient/
├── README.md
├── .env.example
├── .gitignore
├── .dockerignore
├── docker-compose.yml
├── config/
│   └── models.txt
├── data/
│   ├── thesentient.db
│   └── test_verify.db
├── logs/
│   ├── bot_debug_output.txt
│   ├── bot_status.txt
│   ├── test_output_full.txt
│   ├── test_output.txt
│   └── verify_*.log/txt files
├── scripts/
│   ├── __init__.py
│   ├── check/
│   │   ├── __init__.py
│   │   ├── bot_api.py
│   │   ├── bot_config.py
│   │   ├── bots.py
│   │   ├── earnings.py
│   │   └── syntax.py
│   ├── debug/
│   │   ├── __init__.py
│   │   ├── alpaca_conn.py
│   │   └── bot.py
│   ├── list/
│   │   ├── __init__.py
│   │   ├── bots.py
│   │   └── models.py
│   ├── management/
│   │   ├── __init__.py
│   │   ├── reactivate_bot.py
│   │   └── reset_and_trigger.py
│   ├── test/
│   │   ├── __init__.py
│   │   ├── activate_bot.py
│   │   ├── bot_api.py
│   │   ├── bot_orders.py
│   │   ├── bot_status.py
│   │   ├── earnings_bot.py
│   │   ├── gemini_models.py
│   │   ├── liquidation.py
│   │   ├── market_data.py
│   │   ├── order_execution.py
│   │   ├── process_earnings.py
│   │   ├── scheduler_logic.py
│   │   ├── sizing.py
│   │   └── symbol_mapper.py
│   ├── verify/
│   │   ├── __init__.py
│   │   ├── alpaca_env.py
│   │   ├── alpaca_execution.py
│   │   ├── backend.py
│   │   └── env.py
│   ├── db/
│   │   ├── __init__.py
│   │   ├── drop_decisions_table.py
│   │   ├── fix_decisions_table.py
│   │   └── inspect_hex.py
│   ├── utilities/
│   │   ├── __init__.py
│   │   └── read_output.py
│   ├── restart-backend.bat
│   ├── start-dev.bat
│   └── start-dev.sh
├── backend/          (existing)
├── frontend/         (existing)
├── legacy_bot/       (existing)
├── modular/          (new modular system)
├── plans/            (existing)
├── streamlit_app/    (existing)
└── assets/           (existing)
```

## Benefits of This Structure

1. **Clean Root Directory**: Only essential configuration and documentation files remain
2. **Logical Organization**: Files grouped by purpose (check, debug, test, verify, etc.)
3. **Easy Navigation**: Clear directory hierarchy makes it easy to find specific scripts
4. **Scalability**: New scripts can be added to appropriate categories
5. **Maintainability**: Related scripts are grouped together for easier updates
6. **Consistency**: Follows Python package structure with `__init__.py` files

## Implementation Steps

### Phase 1: Prepare Directory Structure
1. Create new directories: `config/`, `data/`, `logs/`
2. Create subdirectories in `scripts/`: `check/`, `debug/`, `list/`, `management/`, `test/`, `verify/`, `db/`, `utilities/`
3. Add `__init__.py` files to make directories importable as Python packages

### Phase 2: Move Files
1. Move database files to `data/`
2. Move log files to `logs/`
3. Move configuration file to `config/`
4. Move batch scripts to `scripts/`
5. Move Python scripts to their respective subdirectories in `scripts/`

### Phase 3: Update References
1. Update any hardcoded paths in scripts that reference moved files
2. Update documentation if it references specific file locations
3. Update `.gitignore` to include new directories if needed

### Phase 4: Verify and Test
1. Test that moved scripts still work correctly
2. Verify database connections still work with new paths
3. Test batch/shell scripts with new locations

## Special Considerations

1. **Database Paths**: The SQLite database `thesentient.db` is referenced by many scripts. Need to update connection strings or use relative paths that work from new locations.

2. **Backward Compatibility**: Some scripts may be called from other tools or scheduled tasks. Consider creating symbolic links or wrapper scripts in the root directory for critical scripts during transition.

3. **Existing `scripts/` Directory**: The existing `scripts/` directory contains 25+ Python files. These should be reviewed and potentially reorganized into the new category structure.

4. **Modular System Integration**: The new `modular/` directory will eventually contain the main application logic, reducing the need for many of these utility scripts.

## Risk Mitigation

1. **Backup**: Create backup of all files before moving
2. **Incremental Move**: Move one category at a time and test
3. **Version Control**: Use git to track changes and allow rollback
4. **Documentation**: Update README with new file locations

## Expected Outcome

After cleanup, the root directory will contain only:
- `README.md`
- Configuration files (`.env.example`, `.gitignore`, `.dockerignore`, `docker-compose.yml`)
- Key directories (`backend/`, `frontend/`, `modular/`, `scripts/`, `data/`, `logs/`, `config/`)

This creates a "comfy to use folder" that is clean, organized, and easy to navigate for both human developers and AI agents.