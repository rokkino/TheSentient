import asyncio
import sys
import os
sys.path.append(os.path.join(os.getcwd(), "backend"))

from src.backend.models.user import get_db
from src.backend.models.bot import Bot
from src.backend.services.bot_service import bot_service
from src.backend.services.earnings_service import EarningsService
import json

async def test_bot():
    print("=== Testing Earnings Bot ===\n")
    
    # Get DB session
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        # Get all bots
        bots = db.query(Bot).all()
        print(f"Found {len(bots)} bot(s) in database:\n")
        
        for bot in bots:
            print(f"Bot ID: {bot.id}")
            print(f"Name: {bot.name}")
            print(f"Type: {bot.bot_type}")
            print(f"Status: {bot.status}")
            print(f"Active: {bot.is_active}")
            
            config = bot.get_config()
            print(f"\nConfiguration:")
            print(f"  Broker: {config.get('broker', 'Not set')}")
            print(f"  IG Username: {'Set' if config.get('ig_username') else 'Not set'}")
            print(f"  IG API Key: {'Set' if config.get('ig_api_key') else 'Not set'}")
            print(f"  Gemini API Key: {'Set' if config.get('gemini_api_key') else 'Not set'}")
            print(f"  Account Type: {config.get('ig_acc_type', 'Not set')}")
            
        # Check today's earnings
        print("\n=== Checking Today's Earnings ===")
        earnings_service = EarningsService()
        earnings = await earnings_service.get_earnings_today_tomorrow()
        
        from datetime import datetime, date
        today = date.today().isoformat()
        today_earnings = [e for e in earnings if e.get('date') == today]
        
        print(f"\nFound {len(today_earnings)} earnings today:")
        for e in today_earnings[:5]:  # Show first 5
            symbol = e.get('symbol', e.get('ticker'))
            company = e.get('company', e.get('companyshortname', symbol))
            time = e.get('time', 'N/A')
            print(f"  {symbol} - {company} at {time}")
        
        if len(today_earnings) > 5:
            print(f"  ... and {len(today_earnings) - 5} more")
            
        # Check if bot is configured
        if bots:
            bot = bots[0]
            if bot.is_configured():
                print(f"\n✅ Bot is configured and ready")
                if bot.is_active:
                    print(f"✅ Bot is ACTIVE and running")
                else:
                    print(f"⚠️  Bot is INACTIVE")
                    print(f"\nTo activate the bot, use the web interface or run:")
                    print(f"  bot_service.activate_bot(db, {bot.id}, {bot.user_id})")
            else:
                print(f"\n❌ Bot is NOT fully configured")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_bot())
