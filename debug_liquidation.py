#!/usr/bin/env python3
"""
Debug liquidation order failures.
"""
import sys
import os
from datetime import datetime, timedelta

BACKEND_DIR = os.path.join(os.getcwd(), "src", "backend", "backend")
sys.path.insert(0, BACKEND_DIR)

from models.user import SessionLocal
from models.bot import Bot, Decision
from models.user import User

db = SessionLocal()
try:
    # Find the bot
    bot = db.query(Bot).filter(Bot.name == 'Earnings Report Genius').first()
    if not bot:
        print("Bot not found")
        sys.exit(1)
    
    print(f"Bot: {bot.name} (ID: {bot.id})")
    print(f"Active: {bot.is_active}")
    
    # Check user Gemini API key
    user = db.query(User).filter(User.id == bot.user_id).first()
    if user:
        print(f"User: {user.username}")
        print(f"Gemini API key present: {bool(user.gemini_api_key)}")
        print(f"Gemini model: {user.gemini_model}")
    else:
        print("No user")
    
    # Check executed BUY decisions (positions that might be open)
    executed_buys = db.query(Decision).filter(
        Decision.bot_id == bot.id,
        Decision.status == 'EXECUTED',
        Decision.decision == 'BUY'
    ).all()
    
    print(f"\nExecuted BUY decisions (potential open positions): {len(executed_buys)}")
    for d in executed_buys:
        # Check if there's a matching executed SELL
        sell = db.query(Decision).filter(
            Decision.bot_id == bot.id,
            Decision.symbol == d.symbol,
            Decision.status == 'EXECUTED',
            Decision.decision == 'SELL',
            Decision.created_at > d.created_at
        ).first()
        age = datetime.now() - (d.executed_at or d.created_at)
        print(f"  {d.symbol}: bought {d.executed_at or d.created_at}, age {age}, closed: {bool(sell)}")
    
    # Check failed liquidation orders
    failed_liquids = db.query(Decision).filter(
        Decision.bot_id == bot.id,
        Decision.status == 'FAILED',
        Decision.reasoning.like('%FORCE LIQUIDATION%')
    ).order_by(Decision.created_at.desc()).limit(5).all()
    
    print(f"\nRecent failed liquidation orders: {len(failed_liquids)}")
    for d in failed_liquids:
        print(f"  {d.symbol}: {d.reasoning}")
        # Extract error
        import re
        error_match = re.search(r'Error: (.*)', d.reasoning or '')
        if error_match:
            print(f"    Error: {error_match.group(1)[:100]}")
    
    # Check pending liquidation orders
    pending_liquids = db.query(Decision).filter(
        Decision.bot_id == bot.id,
        Decision.status == 'PENDING',
        Decision.reasoning.like('%FORCE LIQUIDATION%')
    ).all()
    
    print(f"\nPending liquidation orders: {len(pending_liquids)}")
    for d in pending_liquids:
        print(f"  {d.symbol}: execution time {d.execution_time}")
    
    # Check if there are any actual positions in Alpaca (if Alpaca service available)
    try:
        from services.alpaca_service import AlpacaService
        service = AlpacaService()
        if service.available:
            print("\nChecking Alpaca positions...")
            import asyncio
            async def check():
                try:
                    positions = await service.get_positions()
                    print(f"Alpaca positions: {len(positions)}")
                    for p in positions:
                        print(f"  {p.get('symbol')}: {p.get('qty')} shares, side: {p.get('side')}")
                except Exception as e:
                    print(f"Error getting positions: {e}")
            asyncio.run(check())
        else:
            print("\nAlpaca service not available")
    except Exception as e:
        print(f"\nError importing Alpaca service: {e}")
    
finally:
    db.close()