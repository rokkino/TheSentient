"""
Directly test bot order generation by calling process_bot_earnings.
"""
import asyncio
import os
import sys

# Change to backend directory to ensure correct relative paths
os.chdir(os.path.join(os.path.dirname(__file__), 'backend'))
sys.path.insert(0, '.')

async def test_process_earnings():
    print("=" * 60)
    print("Testing Bot Order Generation")
    print("=" * 60)
    print(f"Working directory: {os.getcwd()}")
    
    # Now check bot status first
    from models.user import SessionLocal
    from models.bot import Bot, Decision
    
    db = SessionLocal()
    bot = db.query(Bot).filter(Bot.id == 1).first()
    if bot:
        print(f"\nBot status: id={bot.id}, name={bot.name}, is_active={bot.is_active}, status={bot.status}")
    else:
        print("Bot 1 not found!")
        return
    db.close()
    
    from services.scheduler_jobs import process_bot_earnings
    
    # Test with bot ID 1
    print("\nTriggering process_bot_earnings for bot 1...")
    await process_bot_earnings(1)
    
    print("\nChecking database for decisions...")
    import sqlite3
    conn = sqlite3.connect('thesentient.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM decisions ORDER BY created_at DESC LIMIT 10')
    rows = cursor.fetchall()
    
    # Get column names
    cursor.execute("PRAGMA table_info(decisions)")
    cols = [info[1] for info in cursor.fetchall()]
    
    print(f"\nFound {len(rows)} decisions:")
    for row in rows:
        row_dict = dict(zip(cols, row))
        print(f"  ID={row_dict['id']} | {row_dict['symbol']} | {row_dict['decision']} | status={row_dict['status']} | exec={row_dict['execution_time']}")
        if row_dict['reasoning']:
            reason = row_dict['reasoning'][:80]
            print(f"    Reason: {reason}...")
    
    conn.close()
    print("\n" + "=" * 60)

if __name__ == "__main__":
    asyncio.run(test_process_earnings())
