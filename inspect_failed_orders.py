#!/usr/bin/env python3
"""
Inspect failed orders and missing new orders.
"""
import sys
import os
from datetime import datetime, timedelta

BACKEND_DIR = os.path.join(os.getcwd(), "src", "backend", "backend")
sys.path.insert(0, BACKEND_DIR)

from models.user import SessionLocal
from models.bot import Decision, Bot

db = SessionLocal()
try:
    # Get total decisions
    total = db.query(Decision).count()
    print(f"Total decisions in database: {total}")
    
    # Status breakdown
    from sqlalchemy import func
    status_counts = db.query(Decision.status, func.count(Decision.id)).group_by(Decision.status).all()
    print("\nStatus breakdown:")
    for status, count in status_counts:
        print(f"  {status}: {count}")
    
    # Failed orders with details
    failed = db.query(Decision).filter(Decision.status == 'FAILED').order_by(Decision.created_at.desc()).limit(20).all()
    print(f"\nRecent failed orders (showing {len(failed)}):")
    for d in failed:
        bot_name = db.query(Bot).filter(Bot.id == d.bot_id).first().name if d.bot_id else "N/A"
        print(f"  ID: {d.id}, Bot: {bot_name}, Symbol: {d.symbol}, Action: {d.decision}")
        print(f"    Created: {d.created_at}, Execution Time: {d.execution_time}")
        print(f"    Reasoning: {d.reasoning[:200] if d.reasoning else 'None'}")
        print()
    
    # Pending decisions
    pending = db.query(Decision).filter(Decision.status == 'PENDING').all()
    print(f"\nPending decisions: {len(pending)}")
    for d in pending[:10]:
        print(f"  ID: {d.id}, Symbol: {d.symbol}, Action: {d.decision}, Execution Time: {d.execution_time}")
    
    # Decisions for tonight/tomorrow (next 48 hours)
    now = datetime.now()
    tomorrow = now + timedelta(days=2)
    upcoming = db.query(Decision).filter(
        Decision.execution_time >= now,
        Decision.execution_time <= tomorrow
    ).all()
    print(f"\nDecisions scheduled for next 48 hours: {len(upcoming)}")
    for d in upcoming:
        print(f"  ID: {d.id}, Symbol: {d.symbol}, Action: {d.decision}, Execution Time: {d.execution_time}, Status: {d.status}")
    
    # Check if there are any decisions for earnings tonight/tomorrow
    # We need to cross-reference with earnings calendar
    from services.earnings_service import earnings_service
    import asyncio
    
    async def check_earnings():
        try:
            # Get earnings for today and tomorrow
            today = datetime.now().date()
            earnings = await earnings_service.get_earnings_calendar(start_date=today.isoformat(), months=0.5, use_cache=True)
            print(f"\nEarnings in calendar (today+15 days): {len(earnings)}")
            # Count symbols
            symbols = [e.get('symbol') for e in earnings if e.get('symbol')]
            print(f"Unique symbols: {len(set(symbols))}")
            
            # See if any of these symbols have decisions
            decisions_for_earnings = db.query(Decision).filter(Decision.symbol.in_(symbols)).all()
            print(f"Decisions for earnings symbols: {len(decisions_for_earnings)}")
        except Exception as e:
            print(f"Error checking earnings: {e}")
    
    asyncio.run(check_earnings())
    
finally:
    db.close()