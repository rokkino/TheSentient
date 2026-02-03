
import sys
import os
import asyncio
import contextlib
from datetime import datetime, date, timedelta, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))
os.environ['DATABASE_URL'] = 'sqlite:///backend/thesentient.db'

# Import services to patch
from services.bot_service import bot_service
from services.gemini_service import GeminiService
from services.earnings_service import earnings_service

# Import DB
from models.bot import Bot, Decision
from models.user import User

# Init DB
engine = create_engine('sqlite:///backend/thesentient.db')
Session = sessionmaker(bind=engine)
session = Session()

# --- MOCKS ---
class MockService:
    async def get_account(self):
        return {'portfolio_value': 10000.0}

async def mock_get_configured_service(db, bot):
    return MockService()

async def mock_analyze_opportunities(self, earnings, market_data, current_time=None):
    # Return 2 opportunities with different confidence
    return [
        {'symbol': 'HIGH_CONF', 'decision': 'BUY', 'confidence_score': 80, 'reasoning': 'Good'},
        {'symbol': 'LOW_CONF', 'decision': 'BUY', 'confidence_score': 40, 'reasoning': 'Okay'}
    ]

async def mock_get_earnings(months=1, use_cache=True):
    # Returns fake earnings for today/tomorrow
    today = (datetime.now() + timedelta(days=2)).date()
    return [
        {
            'symbol': 'HIGH_CONF', 
            'date': today.isoformat(), 
            'time': 'After Market Close',
            'name': 'High Conf Corp'
        },
        {
            'symbol': 'LOW_CONF', 
            'date': today.isoformat(), 
            'time': 'After Market Close',
            'name': 'Low Conf Corp'
        }
    ]

# Apply patches
bot_service._get_configured_service = mock_get_configured_service
GeminiService.analyze_market_opportunities = mock_analyze_opportunities
earnings_service.get_earnings_calendar = mock_get_earnings

async def test_sizing():
    with open("verify_sizing.txt", "w", encoding="utf-8") as log:
        with contextlib.redirect_stdout(log):
            print("=== TEST POSITION SIZING ===")
            
            # 1. Setup Test Bot
            user = session.query(User).first()
            if not user:
                print("No user found")
                return

            test_bot_name = "TEST_SIZING_BOT"
            # Cleanup previous
            old_bot = session.query(Bot).filter(Bot.name == test_bot_name).first()
            if old_bot:
                session.delete(old_bot)
                session.commit()
                
            bot = Bot(
                user_id=user.id,
                name=test_bot_name,
                bot_type='earnings_report_genius',
                is_active=True,
                status='active'
            )
            # CONFIG: 10% daily budget = $1000
            # Sizing: Enabled
            bot.set_config({
                'daily_budget_pct': 10,
                'use_confidence_sizing': True,
                'broker': 'Alpaca',
                'account_id': 999 
            })
            session.add(bot)
            session.commit()
            
            print(f"Created bot {bot.name} with 10% daily budget")
            
            # 2. Run Scheduler Logic
            from services.scheduler_jobs import process_bot_earnings
            
            print("Running process_bot_earnings...")
            await process_bot_earnings(bot.id)
            
            # 3. Verify Decisions
            decisions = session.query(Decision).filter(
                Decision.bot_id == bot.id,
                Decision.status == 'PENDING',
                Decision.decision == 'BUY'
            ).all()
            
            total_allocated = 0
            for d in decisions:
                print(f"Decision {d.symbol}: Allocated ${d.allocated_amount:.2f}")
                total_allocated += d.allocated_amount
            
            print(f"Total Allocated: ${total_allocated:.2f}")
            
            # Check logic
            # Total Confidence = 80 + 40 = 120
            # Budget = 1000
            # HIGH_CONF = 1000 * (80/120) = 666.67
            # LOW_CONF = 1000 * (40/120) = 333.33
            
            high = next((d for d in decisions if d.symbol == 'HIGH_CONF'), None)
            low = next((d for d in decisions if d.symbol == 'LOW_CONF'), None)
            
            if high and abs(high.allocated_amount - 666.67) < 1.0:
                 print("SUCCESS: High confidence allocation correct")
            else:
                 print(f"FAILURE: High confidence allocation wrong (Expected ~666.67, Got {high.allocated_amount if high else 'None'})")
                 
            if low and abs(low.allocated_amount - 333.33) < 1.0:
                 print("SUCCESS: Low confidence allocation correct")
            else:
                 print(f"FAILURE: Low confidence allocation wrong (Expected ~333.33, Got {low.allocated_amount if low else 'None'})")
            
            # Cleanup
            session.query(Decision).filter(Decision.bot_id == bot.id).delete()
            session.delete(bot)
            session.commit()
            print("Cleanup complete")

if __name__ == "__main__":
    asyncio.run(test_sizing())
