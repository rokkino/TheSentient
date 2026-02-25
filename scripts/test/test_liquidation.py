
import sys
import os
import asyncio
from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

# Force backend to use the correct DB
os.environ['DATABASE_URL'] = 'sqlite:///backend/thesentient.db'

from src.backend.models.bot import Bot, Decision
from src.backend.models.user import User

# Init DB
engine = create_engine('sqlite:///backend/thesentient.db')
Session = sessionmaker(bind=engine)
session = Session()

async def test_liquidation():
    import contextlib
    
    with open("verify_log.txt", "w", encoding="utf-8") as log:
        with contextlib.redirect_stdout(log):
            print("=== TEST LIQUIDATION LOGIC ===")
        
            # 1. Setup Test Bot
            user = session.query(User).first()
            if not user:
                print("No user found, creating dummy")
                return
    
            test_bot_name = "TEST_LIQUIDATION_BOT"
            bot = session.query(Bot).filter(Bot.name == test_bot_name).first()
            if not bot:
                bot = Bot(
                    user_id=user.id,
                    name=test_bot_name,
                    bot_type='earnings_report_genius',
                    is_active=True,
                    status='active'
                )
                session.add(bot)
                session.commit()
            
            print(f"Using Bot: {bot.id} {bot.name}")
            
            # 2. Clear old test decisions
            session.query(Decision).filter(Decision.bot_id == bot.id).delete()
            session.commit()
            
            # 3. Create STUCK Position
            # EXECUTION 3 days ago
            old_date = datetime.now(timezone.utc) - timedelta(days=3)
            
            stuck_entry = Decision(
                bot_id=bot.id,
                symbol="STUCK_TICKER",
                decision="BUY",
                status="EXECUTED",
                execution_time=old_date,
                executed_at=old_date,
                created_at=old_date,
                reasoning="Test stuck position"
            )
            session.add(stuck_entry)
            session.commit()
            print(f"Created stuck position: {stuck_entry.symbol} executed at {stuck_entry.executed_at}")
            
            # 4. Run Scheduler Job Logic
            # We import the specific function
            from src.backend.services.scheduler_jobs import process_bot_earnings
            
            print("Running process_bot_earnings...")
            await process_bot_earnings(bot.id)
            
            # 5. Verify Result
            # Re-query
            liquidations = session.query(Decision).filter(
                Decision.bot_id == bot.id,
                Decision.symbol == "STUCK_TICKER",
                Decision.decision == "SELL",
                Decision.reasoning.like("%FORCE LIQUIDATION%")
            ).all()
            
            if liquidations:
                print(f"SUCCESS: Found {len(liquidations)} liquidation orders!")
                for l in liquidations:
                    print(f"  - {l.decision} {l.symbol} @ {l.execution_time} (Status: {l.status})")
                    print(f"    Reason: {l.reasoning}")
            else:
                print("FAILURE: No liquidation order created!")
        
    session.close()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_liquidation())
