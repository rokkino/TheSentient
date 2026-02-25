import os
import sys
import json

backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from models.user import SessionLocal
from models.bot import Bot

def main():
    db = SessionLocal()
    bots = db.query(Bot).all()
    for b in bots:
        print(f"Bot ID: {b.id}, Name: {b.name}")
        print(f"  win_rate: {b.win_rate}, trades: {b.total_trades}, profit: {b.profit}")
        if b.performance_history:
            hist = json.loads(b.performance_history)
            print(f"  history points: {len(hist)}")
            if len(hist) > 0:
                print(f"  first point: {hist[0]}")
                print(f"  last point: {hist[-1]}")
        else:
            print("  history: None")
    db.close()

if __name__ == "__main__":
    main()
