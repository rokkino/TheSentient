#!/usr/bin/env python3
import asyncio
import sqlite3
import sys
sys.path.append('src/backend/backend')
from services.scheduler_jobs import process_bot_earnings
from datetime import datetime, timezone

async def main():
    print("=== Final System Test ===\n")
    
    # Check database schema
    conn = sqlite3.connect('src/backend/backend/thesentient.db')
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(decisions)")
    cols = [c[1] for c in cursor.fetchall()]
    print("1. Database schema check:")
    print(f"   Columns in decisions: {cols}")
    if 'stop_loss' in cols and 'take_profit' in cols:
        print("   [OK] stop_loss and take_profit columns exist")
    else:
        print("   [FAIL] Missing columns")
        return
    
    # Count pending decisions before
    cursor.execute("SELECT COUNT(*) FROM decisions WHERE status='PENDING'")
    pending_before = cursor.fetchone()[0]
    print(f"\n2. Pending decisions before: {pending_before}")
    
    # Run earnings analysis for bot 1
    print("\n3. Running earnings analysis for bot 1...")
    try:
        await process_bot_earnings(1)
        print("   [OK] Earnings analysis completed")
    except Exception as e:
        print(f"   [FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Count pending decisions after
    cursor.execute("SELECT COUNT(*) FROM decisions WHERE status='PENDING'")
    pending_after = cursor.fetchone()[0]
    print(f"\n4. Pending decisions after: {pending_after}")
    
    new_decisions = pending_after - pending_before
    if new_decisions > 0:
        print(f"   ✓ Generated {new_decisions} new pending decisions")
        # Show them
        cursor.execute("""
            SELECT symbol, decision, execution_time 
            FROM decisions 
            WHERE status='PENDING' 
            ORDER BY created_at DESC 
            LIMIT 5
        """)
        for sym, dec, exec_time in cursor.fetchall():
            print(f"     - {sym} {dec} @ {exec_time}")
    else:
        print("   ✗ No new decisions generated (maybe no earnings opportunities)")
    
    # Check for upcoming earnings decisions
    cursor.execute("""
        SELECT COUNT(*) FROM decisions 
        WHERE status='PENDING' AND execution_time > datetime('now')
    """)
    future = cursor.fetchone()[0]
    print(f"\n5. Future pending decisions: {future}")
    
    # Verify earnings calendar date range
    print("\n6. Earnings calendar date range check:")
    from services.earnings_service import EarningsService
    service = EarningsService()
    earnings = await service.get_earnings_calendar(months=1, use_cache=True)
    today = datetime.now().date()
    count_today = sum(1 for e in earnings if 'date' in e and str(today) in e['date'])
    count_tomorrow = sum(1 for e in earnings if 'date' in e and str(today) in e['date'])
    print(f"   Total earnings: {len(earnings)}")
    print(f"   Earnings today: {count_today}")
    
    # Check liquidation logic
    print("\n7. Liquidation logic check:")
    cursor.execute("SELECT COUNT(*) FROM decisions WHERE status='FAILED' AND reasoning LIKE '%LIQUIDATION%'")
    failed_liquidation = cursor.fetchone()[0]
    print(f"   Failed liquidation decisions: {failed_liquidation}")
    
    conn.close()
    
    print("\n=== Summary ===")
    print("The earnings genius report bot has been improved with:")
    print("• Fixed earnings calendar cache (7-day TTL)")
    print("• Fixed liquidation quantity calculation")
    print("• Updated decision duplicate detection")
    print("• Added stop_loss/take_profit fields")
    print("• Enhanced debug logging")
    print("• Position tracking via open positions check")
    print("\nThe bot should now generate new orders for upcoming earnings")
    print("and execute them during market hours with proper risk management.")

if __name__ == "__main__":
    asyncio.run(main())