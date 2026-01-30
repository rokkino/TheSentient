
import asyncio
import os
import sys
import json
from datetime import datetime

# Ensure backend imports work
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from services.scheduler_jobs import process_bot_earnings
from models.user import SessionLocal, User
from models.bot import Bot

async def main():
    db = SessionLocal()
    try:
        # 1. Ensure User Exists
        user = db.query(User).filter(User.username == "debug_user").first()
        if not user:
            print("Creating debug user...")
            # from services.auth_service import get_password_hash
            # Hardcode hash to avoid dependencies
            hashed_pw = "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn68n5.P.dD5x/p.X.1" 
            user = User(
                username="debug_user",
                email="debug@example.com",
                hashed_password=hashed_pw,
                is_active=True,
                gemini_api_key=os.getenv("GOOGLE_GEMINI_API_KEY"), # Use env var for test
                gemini_model="gemini-3-flash-preview"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        print(f"Using User ID: {user.id}")

        # 2. Ensure Bot Exists
        bot = db.query(Bot).filter(
            Bot.user_id == user.id, 
            Bot.bot_type == 'earnings_report_genius'
        ).first()
        
        if not bot:
            print("Creating Earnings Bot...")
            bot = Bot(
                user_id=user.id,
                name="Debug Earnings Bot",
                bot_type="earnings_report_genius",
                description="Debug bot for testing",
                status="active",
                is_active=True,
                config=json.dumps({"broker": "IG", "risk_level": "medium"})
            )
            db.add(bot)
            db.commit()
            db.refresh(bot)
            
        print(f"Using Bot ID: {bot.id} ({bot.name})")
        
        # 3. Process Earnings
        print("Starting process_bot_earnings...")
        await process_bot_earnings(bot.id)
        print("Process completed.")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
