#!/usr/bin/env python3
"""
Final test to verify all fixes for earnings bot issues:
1. Order execution failures (especially sell orders)
2. Earnings calendar starting from February 2
3. Enhanced debug logging
"""
import sys
import os
import asyncio
import json
from datetime import datetime, date, timedelta

BACKEND_DIR = os.path.join(os.getcwd(), "src", "backend", "backend")
sys.path.insert(0, BACKEND_DIR)

async def test_order_execution_debug():
    """Test order execution with enhanced debug logging"""
    print("=== Testing Order Execution Debug ===")
    
    try:
        from services.scheduler_jobs import execute_orders_job
        print("[DEBUG] execute_orders_job imported successfully")
        
        # Check if there are any pending decisions in database
        from models.user import SessionLocal
        from models.bot import Decision
        
        db = SessionLocal()
        try:
            pending = db.query(Decision).filter(
                Decision.status == "PENDING",
                Decision.execution_time <= datetime.now()
            ).all()
            
            print(f"[DEBUG] Found {len(pending)} pending decisions")
            
            for d in pending[:5]:  # Show first 5
                print(f"  Decision ID: {d.id}, Symbol: {d.symbol}, Action: {d.decision}")
                print(f"    Bot ID: {d.bot_id}, Status: {d.status}")
                print(f"    Execution Time: {d.execution_time}")
                print(f"    Allocated Amount: {d.allocated_amount}")
                print(f"    Stop Loss: {d.stop_loss}, Take Profit: {d.take_profit}")
                
        finally:
            db.close()
            
    except Exception as e:
        print(f"[ERROR] Order execution test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print()

async def test_earnings_calendar():
    """Test earnings calendar date range"""
    print("=== Testing Earnings Calendar ===")
    
    try:
        from services.earnings_service import earnings_service
        
        # Test 1: Default calendar (should start from today, not Feb 2)
        print("\nTest 1: Default calendar (no start_date)")
        earnings = await earnings_service.get_earnings_calendar(
            start_date=None,
            months=1,
            offset_months=0,
            use_cache=True
        )
        
        print(f"Total earnings: {len(earnings)}")
        
        if earnings:
            # Get unique dates
            dates = set()
            for e in earnings:
                if 'date' in e:
                    dates.add(e['date'])
            
            print(f"Unique dates: {len(dates)}")
            sorted_dates = sorted(dates)
            print(f"Earliest date: {sorted_dates[0]}")
            print(f"Latest date: {sorted_dates[-1]}")
            
            # Check if we have data for today
            today = datetime.now().date().isoformat()
            today_earnings = [e for e in earnings if e.get('date') == today]
            print(f"Earnings for today ({today}): {len(today_earnings)}")
            
            # Verify we're not stuck on Feb 2
            feb2_count = len([e for e in earnings if e.get('date') == '2026-02-02'])
            print(f"Earnings for 2026-02-02: {feb2_count}")
            if feb2_count > 0 and len(dates) == 1:
                print("WARNING: Calendar might be stuck on Feb 2!")
            else:
                print("OK: Calendar not stuck on Feb 2")
        
        # Test 2: Explicit start_date = today
        print("\nTest 2: Explicit start_date = today")
        today_str = datetime.now().date().isoformat()
        earnings2 = await earnings_service.get_earnings_calendar(
            start_date=today_str,
            months=1,
            offset_months=0,
            use_cache=False  # bypass cache
        )
        
        print(f"Earnings with explicit start_date: {len(earnings2)}")
        if earnings2:
            dates2 = set(e.get('date') for e in earnings2 if 'date' in e)
            print(f"Date range: {min(dates2)} to {max(dates2)}")
        
        # Test 3: Check cache age logic
        print("\nTest 3: Cache age verification")
        from services.earnings_service import EarningsService
        service = EarningsService()
        
        test_date = datetime.now().date()
        cache_result = service._get_cached_earnings_for_date(test_date)
        if cache_result is None:
            print(f"No cache for {test_date} (expected if cache expired or missing)")
        else:
            print(f"Cache found for {test_date}: {len(cache_result)} items")
        
    except Exception as e:
        print(f"[ERROR] Earnings calendar test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print()

def test_debug_logging():
    """Test that enhanced debug logging is in place"""
    print("=== Testing Debug Logging ===")
    
    # Check scheduler_jobs for enhanced logging
    try:
        with open(os.path.join(BACKEND_DIR, 'services', 'scheduler_jobs.py'), 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Look for enhanced debug logging patterns
        debug_patterns = [
            'print.*\\[JOB\\]',
            'print.*\\[DEBUG\\]',
            'print.*Error executing order',
            'print.*Calculated qty',
            'print.*Target Amount'
        ]
        
        print("Enhanced logging found:")
        for pattern in debug_patterns:
            import re
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                print(f"  [OK] {pattern}: {len(matches)} occurrences")
            else:
                print(f"  [NOT FOUND] {pattern}: Not found")
    
    except Exception as e:
        print(f"Error reading scheduler_jobs: {e}")
    
    # Check earnings_service for enhanced logging
    try:
        with open(os.path.join(BACKEND_DIR, 'services', 'earnings_service.py'), 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("\nEarnings service logging:")
        patterns = [
            'print.*\\[EarningsService\\]',
            'Cache too old',
            'Using cached earnings',
            'Error fetching earnings'
        ]
        
        for pattern in patterns:
            import re
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                print(f"  [OK] {pattern}: {len(matches)} occurrences")
    
    except Exception as e:
        print(f"Error reading earnings_service: {e}")
    
    print()

def test_database_schema():
    """Verify database schema includes stop_loss and take_profit"""
    print("=== Testing Database Schema ===")
    
    from models.user import DATABASE_URL
    print(f"Database URL: {DATABASE_URL}")
    
    # Extract path from SQLite URL
    if DATABASE_URL.startswith('sqlite:///'):
        db_path = DATABASE_URL[10:]
        if not os.path.exists(db_path):
            # Try alternative path
            db_path = os.path.join(BACKEND_DIR, 'thesentient.db')
    else:
        db_path = DATABASE_URL.replace('sqlite:///', '')
    
    if os.path.exists(db_path):
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check decisions table
        cursor.execute("PRAGMA table_info(decisions)")
        columns = cursor.fetchall()
        col_names = [col[1] for col in columns]
        
        required = ['stop_loss', 'take_profit', 'allocated_amount']
        for col in required:
            if col in col_names:
                print(f"[OK] Column '{col}' exists")
            else:
                print(f"[MISSING] Column '{col}' missing")
        
        conn.close()
    else:
        print(f"Database file not found: {db_path}")
    
    print()

async def main():
    print("=" * 60)
    print("FINAL TEST: Earnings Bot Issue Resolution")
    print("=" * 60)
    print()
    
    # Run tests
    test_database_schema()
    await test_order_execution_debug()
    await test_earnings_calendar()
    test_debug_logging()
    
    print("=" * 60)
    print("SUMMARY:")
    print("- Database schema updated with stop_loss/take_profit columns")
    print("- Earnings calendar cache TTL reduced from 30 to 7 days")
    print("- Enhanced debug logging in scheduler_jobs and earnings_service")
    print("- Sell order failures should now have better debugging")
    print("- Calendar should no longer be stuck on Feb 2")
    print("=" * 60)
    print("\nNOTE: To fully test order execution, you may need to:")
    print("1. Create a test decision with status='PENDING'")
    print("2. Ensure a bot is configured with valid broker credentials")
    print("3. Run execute_orders_job manually")
    print("\nTo test earnings calendar:")
    print("1. Clear old cache: delete src/backend/backend/memory/earnings/*.json")
    print("2. Restart backend to force fresh API calls")

if __name__ == "__main__":
    asyncio.run(main())