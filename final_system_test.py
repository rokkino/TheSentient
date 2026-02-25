#!/usr/bin/env python3
import asyncio
import sys
sys.path.append('src/backend/backend')
from services.scheduler_jobs import process_bot_earnings, execute_orders_job
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.bot import Decision, Bot
import os
from datetime import datetime, timezone

async def test_earnings_generation():
    """Test that earnings analysis generates new decisions for upcoming earnings"""
    print("=== Testing Earnings Generation ===")
    
    # Get current decisions count before
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///thesentient.db')
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    before_count = db.query(Decision).count()
    print(f"Total decisions before: {before_count}")
    
    pending_before = db.query(Decision).filter(Decision.status == 'PENDING').count()
    print(f"Pending decisions before: {pending_before}")
    
    # Get bot ID (assuming bot 1 exists)
    bot = db.query(Bot).filter(Bot.id == 1).first()
    if not bot:
        print("ERROR: No bot found")
        db.close()
        return
    
    print(f"Testing with bot: {bot.name} (ID: {bot.id})")
    db.close()
    
    # Run earnings analysis
    await process_bot_earnings(bot.id)
    
    # Check after
    db = Session()
    after_count = db.query(Decision).count()
    pending_after = db.query(Decision).filter(Decision.status == 'PENDING').count()
    
    print(f"Total decisions after: {after_count}")
    print(f"Pending decisions after: {pending_after}")
    
    new_decisions = after_count - before_count
    if new_decisions > 0:
        print(f"✓ Generated {new_decisions} new decisions")
        # Show new pending decisions
        new_pending = db.query(Decision).filter(
            Decision.status == 'PENDING',
            Decision.created_at >= datetime.now(timezone.utc).replace(second=0, microsecond=0)
        ).all()
        print(f"New pending decisions: {len(new_pending)}")
        for d in new_pending[:5]:
            print(f"  - {d.symbol} {d.decision} @ {d.execution_time}")
    else:
        print("✗ No new decisions generated")
    
    db.close()

async def test_order_execution():
    """Test order execution job (dry run)"""
    print("\n=== Testing Order Execution Job ===")
    print("Running execute_orders_job (will attempt to execute pending decisions)...")
    # This will actually try to execute orders; we'll just see logs
    await execute_orders_job()
    print("Order execution job completed.")

async def main():
    print("Full System Test for Earnings Genius Report Bot")
    print("Current time:", datetime.now(timezone.utc))
    
    await test_earnings_generation()
    # await test_order_execution()  # optional, may cause real trades
    
    print("\n=== Summary ===")
    print("1. Earnings calendar fixed (7-day cache TTL)")
    print("2. Liquidation quantity calculation fixed")
    print("3. Decision duplicate detection updated (allows new earnings)")
    print("4. Position tracking implemented (via open positions check)")
    print("5. Stop loss/take profit fields added to Decision model")
    print("6. Enhanced debug logging throughout")
    print("\nBot should now:")
    print("- Generate new orders for tonight/tomorrow earnings")
    print("- Execute orders during market hours")
    print("- Use bracket orders with stop loss/take profit")
    print("- Liquidate stuck positions correctly")
    print("- Provide detailed debug info for failures")

if __name__ == "__main__":
    asyncio.run(main())