
import sys
import os
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from models.bot import Bot, Decision

# Init DB
engine = create_engine('sqlite:///backend/thesentient.db')
Session = sessionmaker(bind=engine)
session = Session()

print("=== BOTS ===")
bots = session.query(Bot).all()
for bot in bots:
    print(f"ID: {bot.id}, Name: {bot.name}, Type: {bot.bot_type}, Active: {bot.is_active}, Configured: {bot.is_configured()}")
    
    if bot.bot_type == 'earnings_report_genius':
        print(f"--- Recent Decisions for Bot {bot.id} ---")
        decisions = session.query(Decision).filter(Decision.bot_id == bot.id).order_by(Decision.created_at.desc()).limit(20).all()
        for d in decisions:
            exec_time = d.execution_time
            now = datetime.now()
            status_extra = ""
            if d.status == 'PENDING' and exec_time and exec_time < now:
                status_extra = " [LATE! Should have executed]"
                
            print(f"  [{d.id}] {d.symbol} {d.decision} - Status: {d.status}{status_extra}")
            print(f"     Created: {d.created_at}, Exec Time: {d.execution_time}")
            print(f"     Reasoning: {d.reasoning[:100]}...")

print("\n=== PENDING DECISIONS (ALL BOTS) ===")
pending = session.query(Decision).filter(Decision.status == 'PENDING').all()
for p in pending:
     print(f"  Bot {p.bot_id}: {p.symbol} {p.decision} @ {p.execution_time} (Now: {datetime.now()})")

session.close()
