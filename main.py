#!/usr/bin/env python3
"""
The Sentient - Modular Trading System
Primary entry point for the modular architecture.
"""

import os
import sys
from pathlib import Path

def run_modular_system():
    """Run the new modular system"""
    try:
        # Add src to path for imports
        SRC_DIR = Path(__file__).parent / "src"
        sys.path.insert(0, str(SRC_DIR))
        
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
        SRC_DIR = Path(__file__).parent / "src"
        sys.path.insert(0, str(SRC_DIR))
        from src.backend.main import app as legacy_app
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
        print("\nAvailable systems:")
        print("1. Modular System (new) - src/modular/")
        print("2. Legacy Backend - src/backend/")
        print("3. Legacy Bot - src/legacy_bot/")
        print("4. Streamlit App - src/streamlit_app/")
        print("\nTo run a specific system, navigate to its directory:")
        print("  cd src/backend && python -m uvicorn main:app --reload")
        print("  cd src/legacy_bot && python main.py")
        print("  cd src/streamlit_app && streamlit run app.py")
        print("\nOr use the provided scripts:")
        print("  python scripts/start-dev.bat")
        print("  ./scripts/start-dev.sh")
        sys.exit(1)
    
    # Run the application
    import uvicorn
    uvicorn.run(app, host=args.host, port=args.port)

if __name__ == "__main__":
    main()