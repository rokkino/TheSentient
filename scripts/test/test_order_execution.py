"""
Test order execution with Alpaca
Creates a test decision and verifies it gets executed
"""
import sys
import os
import asyncio
from datetime import datetime, timedelta

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

async def test_order_execution():
    print("=" * 60)
    print("Testing Order Execution on Alpaca")
    print("=" * 60)
    
    from src.backend.models.user import SessionLocal
    from src.backend.models.bot import Bot, Decision
    from src.backend.services.scheduler_jobs import execute_orders_job
    
    db = SessionLocal()
    
    try:
        # Find an active bot
        bot = db.query(Bot).filter(Bot.is_active == True).first()
        if not bot:
            print("❌ No active bot found. Please activate a bot first.")
            return
        
        print(f"✓ Found active bot: {bot.name} (ID: {bot.id})")
        
        # Create a test decision with execution time in the past (so it executes immediately)
        test_decision = Decision(
            bot_id=bot.id,
            symbol="AAPL",  # Use a well-known stock
            decision="BUY",
            reasoning="TEST ORDER - This is a test order to verify Alpaca execution works",
            execution_time=datetime.now() - timedelta(minutes=1),  # 1 minute ago
            status="PENDING"
        )
        
        db.add(test_decision)
        db.commit()
        db.refresh(test_decision)
        
        print(f"✓ Created test decision: BUY AAPL (ID: {test_decision.id})")
        print(f"  Execution time: {test_decision.execution_time}")
        print(f"  Status: {test_decision.status}")
        
        # Run the execute_orders_job
        print("\n🔄 Running execute_orders_job...")
        await execute_orders_job()
        
        # Refresh and check status
        db.refresh(test_decision)
        
        print(f"\n📊 After execution:")
        print(f"  Status: {test_decision.status}")
        print(f"  Executed at: {test_decision.executed_at}")
        print(f"  Reasoning: {test_decision.reasoning}")
        
        if test_decision.status == "EXECUTED":
            print("\n✅ SUCCESS! Order was executed on Alpaca")
            print("   Check your Alpaca paper trading dashboard to verify")
        elif test_decision.status == "FAILED":
            print(f"\n❌ FAILED: {test_decision.reasoning}")
        else:
            print(f"\n⚠️  Unexpected status: {test_decision.status}")
        
        # Clean up test decision
        print("\n🧹 Cleaning up test decision...")
        db.delete(test_decision)
        db.commit()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    asyncio.run(test_order_execution())
