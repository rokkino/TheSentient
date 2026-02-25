#!/usr/bin/env python3
"""
Test earnings analysis job manually.
"""
import sys
import os
import asyncio
from datetime import datetime, timedelta

BACKEND_DIR = os.path.join(os.getcwd(), "src", "backend", "backend")
sys.path.insert(0, BACKEND_DIR)

from models.user import SessionLocal
from models.bot import Bot, Decision
from models.user import User
from services.scheduler_jobs import process_bot_earnings

async def test():
    db = SessionLocal()
    try:
        bot = db.query(Bot).filter(Bot.name == 'Earnings Report Genius').first()
        if not bot:
            print("Bot not found")
            return
        
        print(f"Testing earnings analysis for bot: {bot.name} (ID: {bot.id})")
        print(f"Active: {bot.is_active}")
        
        user = db.query(User).filter(User.id == bot.user_id).first()
        if user:
            print(f"User: {user.username}")
            print(f"Gemini API key present: {bool(user.gemini_api_key)}")
            print(f"Gemini model: {user.gemini_model}")
        else:
            print("No user found")
        
        # Count current decisions
        decisions = db.query(Decision).filter(Decision.bot_id == bot.id).count()
        print(f"Existing decisions: {decisions}")
        
        # Run earnings analysis
        print("\nRunning process_bot_earnings...")
        await process_bot_earnings(bot.id)
        
        # Check new decisions
        db2 = SessionLocal()
        new_decisions = db2.query(Decision).filter(Decision.bot_id == bot.id).count()
        db2.close()
        
        print(f"Decisions after analysis: {new_decisions}")
        if new_decisions > decisions:
            print(f"Created {new_decisions - decisions} new decisions")
            # Show new decisions
            db3 = SessionLocal()
            new = db3.query(Decision).filter(Decision.bot_id == bot.id).order_by(Decision.id.desc()).limit(5).all()
            for d in new:
                print(f"  ID: {d.id}, Symbol: {d.symbol}, Action: {d.decision}, Status: {d.status}, Execution: {d.execution_time}")
            db3.close()
        else:
            print("No new decisions created")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test())