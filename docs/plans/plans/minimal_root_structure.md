# Minimal Root Directory Structure

## Goal
Create a clean root directory with only `main.py` as the primary entry point, moving all other files to appropriate subdirectories.

## Proposed Root Directory
```
TheSentient/
├── main.py                    # Primary entry point (modular system)
├── README.md                  # Project documentation
├── .gitignore                # Git ignore rules
├── .dockerignore             # Docker ignore rules
├── .env.example              # Environment template
├── docker-compose.yml        # Docker orchestration
├── requirements.txt          # Python dependencies (or move to config/)
└── pyproject.toml            # Modern Python project config (optional)
```

## Subdirectory Structure
All other files move to these subdirectories:

### 1. `src/` - Source Code
```
src/
├── modular/                  # New modular system
│   ├── core/                # Core framework
│   ├── modules/             # Tab modules (news.py, bot.py, etc.)
│   ├── folderbot/           # Individual bot implementations
│   ├── adapters/            # Service adapters
│   └── api/                 # API endpoints
├── backend/                 # Existing FastAPI backend (transitional)
├── frontend/                # Vue.js frontend
├── legacy_bot/              # Legacy trading bot
└── streamlit_app/           # Streamlit application
```

### 2. `scripts/` - Utility Scripts
```
scripts/
├── check/                   # Verification scripts
├── debug/                   # Debugging tools
├── list/                    # Listing utilities
├── management/              # System management
├── test/                    # Test scripts
├── verify/                  # Verification tools
├── db/                      # Database utilities
└── utilities/               # General utilities
```

### 3. `config/` - Configuration
```
config/
├── models.txt              # Model configurations
├── settings.yaml           # Application settings
└── environment/            # Environment-specific configs
```

### 4. `data/` - Data Files
```
data/
├── databases/              # SQLite databases
├── logs/                   # Application logs
├── uploads/                # User uploads
└── cache/                  # Cached data
```

### 5. `docs/` - Documentation
```
docs/
├── plans/                  # Planning documents
├── api/                    # API documentation
└── architecture/           # Architecture diagrams
```

### 6. `assets/` - Static Assets
```
assets/
├── images/                 # Image files
├── icons/                  # Icon files
└── fonts/                  # Font files
```

## Migration Strategy

### Phase 1: Create New Structure
1. Create all target directories
2. Move files according to the structure above
3. Update import paths in Python files

### Phase 2: Create Root `main.py`
Create a minimal entry point that:
1. Imports from the modular system in `src/modular/`
2. Provides backward compatibility with existing `backend/main.py`
3. Can run both the modular system and legacy system

### Phase 3: Update References
1. Update Dockerfile to use new paths
2. Update batch/shell scripts
3. Update documentation
4. Update CI/CD pipelines

## Root `main.py` Design

```python
#!/usr/bin/env python3
"""
The Sentient - Modular Trading System
Entry point for the modular architecture.
"""

import os
import sys
from pathlib import Path

# Add src to path for imports
SRC_DIR = Path(__file__).parent / "src"
sys.path.insert(0, str(SRC_DIR))

def run_modular_system():
    """Run the new modular system"""
    try:
        from modular.core.module_registry import ModuleRegistry
        from modular.core.event_bus import EventBus
        from modular.api.router import create_app
        
        print("Initializing modular system...")
        
        # Initialize core components
        event_bus = EventBus()
        module_registry = ModuleRegistry(event_bus=event_bus)
        
        # Load configuration
        config_path = Path("config") / "settings.yaml"
        
        # Load modules
        module_registry.discover_modules()
        module_registry.initialize_all()
        
        # Create FastAPI app
        app = create_app(module_registry)
        
        print(f"Modular system initialized with {len(module_registry.modules)} modules")
        return app
        
    except ImportError as e:
        print(f"Modular system not available: {e}")
        print("Falling back to legacy backend...")
        return None

def run_legacy_backend():
    """Run the legacy backend for compatibility"""
    try:
        # Import the existing backend
        sys.path.insert(0, str(SRC_DIR / "backend"))
        from backend.main import app as legacy_app
        print("Running legacy backend...")
        return legacy_app
    except ImportError as e:
        print(f"Legacy backend not available: {e}")
        return None

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="The Sentient Trading System")
    parser.add_argument("--modular", action="store_true", help="Use modular system")
    parser.add_argument("--legacy", action="store_true", help="Use legacy backend")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    
    args = parser.parse_args()
    
    # Determine which system to run
    if args.modular:
        app = run_modular_system()
    elif args.legacy:
        app = run_legacy_backend()
    else:
        # Auto-detect: try modular first, fallback to legacy
        app = run_modular_system()
        if app is None:
            app = run_legacy_backend()
    
    if app is None:
        print("ERROR: No system available to run")
        sys.exit(1)
    
    # Run the application
    import uvicorn
    uvicorn.run(app, host=args.host, port=args.port)

if __name__ == "__main__":
    main()
```

## Backward Compatibility

To maintain backward compatibility:
1. Keep `backend/` directory accessible via imports
2. Create symbolic links or redirects for critical paths
3. Update environment variables to point to new locations
4. Provide migration script for existing installations

## File Movement Plan

### Files to Keep in Root:
- `main.py` (new)
- `README.md`
- `.gitignore`
- `.dockerignore`
- `.env.example`
- `docker-compose.yml`
- `requirements.txt` (or move to config/)

### Files to Move:
1. **Python scripts** → `scripts/` subdirectories
2. **Database files** → `data/databases/`
3. **Log files** → `data/logs/`
4. **Configuration** → `config/`
5. **Source code** → `src/`
6. **Documentation** → `docs/`

## Benefits

1. **Clean root** - Easy to navigate and understand
2. **Modular entry** - Single point of entry for the entire system
3. **Separation of concerns** - Different types of files in appropriate directories
4. **Scalability** - Easy to add new components
5. **Maintainability** - Clear structure for developers and AI agents

## Implementation Steps

1. Create the directory structure
2. Move files to new locations
3. Create root `main.py`
4. Update import paths in all Python files
5. Test that everything works
6. Update documentation
7. Commit changes