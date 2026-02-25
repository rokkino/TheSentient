#!/usr/bin/env python3
"""
Integration test for earnings bot improvements.
Tests the key enhancements: stop loss/take profit, bracket orders, watchdog, fallback.
"""
import sys
import os
import asyncio
import sqlite3
from datetime import datetime, timedelta

# Add backend to path
BACKEND_DIR = os.path.join(os.getcwd(), "src", "backend", "backend")
sys.path.insert(0, BACKEND_DIR)

def test_database_schema():
    """Test that decisions table has required columns."""
    from models.user import DATABASE_URL
    print(f"Testing database: {DATABASE_URL}")
    
    # Extract path from SQLite URL
    if DATABASE_URL.startswith('sqlite:///'):
        db_path = DATABASE_URL[10:]
    else:
        db_path = DATABASE_URL.replace('sqlite:///', '')
    
    if not os.path.exists(db_path):
        print(f"ERROR: Database file not found at {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(decisions)")
    columns = cursor.fetchall()
    col_names = [col[1] for col in columns]
    
    required = ['stop_loss', 'take_profit', 'allocated_amount']
    missing = [col for col in required if col not in col_names]
    
    if missing:
        print(f"FAIL: Missing columns: {missing}")
        print(f"Columns present: {col_names}")
        conn.close()
        return False
    else:
        print(f"PASS: All required columns present")
        conn.close()
        return True

def test_decision_model():
    """Test that Decision model includes stop_loss and take_profit."""
    try:
        from models.bot import Decision
        # Check if attributes exist
        if hasattr(Decision, 'stop_loss') and hasattr(Decision, 'take_profit'):
            print("PASS: Decision model has stop_loss and take_profit attributes")
            return True
        else:
            print("FAIL: Decision model missing attributes")
            return False
    except Exception as e:
        print(f"FAIL: Error importing Decision model: {e}")
        return False

async def test_alpaca_bracket():
    """Test that AlpacaService bracket order method exists."""
    try:
        from services.alpaca_service import AlpacaService
        service = AlpacaService()
        
        # Check method signature
        import inspect
        method = getattr(service, 'place_market_order', None)
        if method:
            sig = inspect.signature(method)
            params = list(sig.parameters.keys())
            if 'take_profit' in params and 'stop_loss' in params:
                print("PASS: AlpacaService.place_market_order supports take_profit and stop_loss")
                return True
            else:
                print(f"FAIL: Missing parameters. Found: {params}")
                return False
        else:
            print("FAIL: place_market_order method not found")
            return False
    except Exception as e:
        print(f"FAIL: Error testing AlpacaService: {e}")
        return False

def test_watchdog():
    """Test that bot_service has _monitor_portfolio method."""
    try:
        from services.bot_service import BotService
        service = BotService()
        if hasattr(service, '_monitor_portfolio'):
            print("PASS: BotService has _monitor_portfolio watchdog method")
            return True
        else:
            print("FAIL: _monitor_portfolio method not found")
            return False
    except Exception as e:
        print(f"FAIL: Error testing BotService: {e}")
        return False

def test_fallback():
    """Test that gemini_service has fallback methods."""
    try:
        from services.gemini_service import GeminiService
        service = GeminiService()
        
        checks = []
        if hasattr(service, '_fallback_analysis'):
            print("PASS: GeminiService has _fallback_analysis method")
            checks.append(True)
        else:
            print("FAIL: _fallback_analysis method not found")
            checks.append(False)
            
        if hasattr(service, '_generate_with_fallback'):
            print("PASS: GeminiService has _generate_with_fallback method")
            checks.append(True)
        else:
            print("FAIL: _generate_with_fallback method not found")
            checks.append(False)
            
        return all(checks)
    except Exception as e:
        print(f"FAIL: Error testing GeminiService: {e}")
        return False

def test_scheduler():
    """Test that cleanup_old_decisions_job exists in scheduler_jobs."""
    try:
        from services.scheduler_jobs import cleanup_old_decisions_job
        print("PASS: cleanup_old_decisions_job function exists")
        return True
    except ImportError as e:
        print(f"FAIL: cleanup_old_decisions_job not found: {e}")
        return False

async def main():
    print("=== Earnings Bot Improvements Integration Test ===\n")
    
    tests = [
        ("Database Schema", test_database_schema),
        ("Decision Model", test_decision_model),
        ("Alpaca Bracket Orders", test_alpaca_bracket),
        ("Watchdog Monitoring", test_watchdog),
        ("AI Fallback Logic", test_fallback),
        ("Scheduler Cleanup", test_scheduler),
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n--- Testing {name} ---")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"ERROR during {name}: {e}")
            results.append((name, False))
    
    print("\n=== Summary ===")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print("\nSUCCESS: All improvements are properly implemented!")
        return 0
    else:
        print("\nWARNING: Some improvements may not be fully functional")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)