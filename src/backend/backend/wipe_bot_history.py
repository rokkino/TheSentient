import os
import sys

backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from models.user import SessionLocal
from models.bot import Bot
import asyncio

def main():
    db = SessionLocal()
    bots = db.query(Bot).all()
    for b in bots:
        print(f"Wiping history for Bot {b.id}: {b.name}")
        b.performance_history = "[]"
        db.add(b)
    db.commit()
    db.close()
    print("History wiped.")

if __name__ == "__main__":
    main()
