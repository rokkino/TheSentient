import sys
from backend.database import SessionLocal
from backend.models.bot import Decision

db = SessionLocal()
failed = db.query(Decision).filter(Decision.status == 'FAILED').order_by(Decision.created_at.desc()).limit(10).all()

for d in failed:
    # Print the ID, symbol, status, decision, execution time, and reasoning
    print(f"[{d.id}] {d.symbol} - {d.decision} - {d.status} - {d.reasoning[-80:] if d.reasoning else ''}")
