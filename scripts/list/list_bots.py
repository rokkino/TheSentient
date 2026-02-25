
import os
import sys

# Ensure backend imports work
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from src.backend.models.user import SessionLocal
from src.backend.models.bot import Bot

def list_bots():
    db = SessionLocal()
    try:
        bots = db.query(Bot).all()
        print(f"Total Bots: {len(bots)}")
        for bot in bots:
            print(f"ID: {bot.id}, Name: {bot.name}, Type: {bot.bot_type}, Active: {bot.is_active}")
    finally:
        db.close()

if __name__ == "__main__":
    list_bots()
