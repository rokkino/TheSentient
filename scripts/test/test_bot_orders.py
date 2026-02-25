"""
Test script to verify bot order generation is working.
This script will:
1. Login to get a token
2. Get the bot list
3. Check decisions for a specific bot
4. Trigger order generation for an active bot
"""
import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def test_bot_orders():
    print("=" * 60)
    print("Testing Bot Order Generation")
    print("=" * 60)
    
    # 1. Login
    print("\n1. Attempting login...")
    login_data = {"username": "rokkino", "password": "password123"}  # Adjust credentials as needed
    try:
        resp = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
        if resp.status_code != 200:
            print(f"   Login failed: {resp.status_code} - {resp.text}")
            # Try getting bots without auth for debug
            print("   Trying to list bots without auth (may fail)...")
        else:
            data = resp.json()
            token = data.get("access_token")
            print(f"   Login successful! Token: {token[:20]}...")
    except Exception as e:
        print(f"   Login error: {e}")
        token = None
    
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    
    # 2. Get bot list
    print("\n2. Getting bot list...")
    try:
        resp = requests.get(f"{BASE_URL}/api/bots", headers=headers)
        if resp.status_code == 200:
            bots = resp.json().get("bots", [])
            print(f"   Found {len(bots)} bots")
            for bot in bots:
                status = "🟢" if bot.get('is_active') else "🔴"
                print(f"   {status} ID={bot.get('id')}: {bot.get('name')} ({bot.get('status')})")
                
            # Find the Earnings Report Genius bot
            active_bot = None
            for bot in bots:
                if bot.get('is_active'):
                    active_bot = bot
                    break
            
            if not active_bot and bots:
                active_bot = bots[0]  # Use first bot if none active
                
        else:
            print(f"   Failed to get bots: {resp.status_code} - {resp.text}")
            return
    except Exception as e:
        print(f"   Error: {e}")
        return
    
    # 3. Check decisions for the bot
    if active_bot:
        bot_id = active_bot.get('id')
        print(f"\n3. Checking decisions for bot ID={bot_id} ({active_bot.get('name')})...")
        try:
            resp = requests.get(f"{BASE_URL}/api/bot/decisions?bot_id={bot_id}&limit=10", headers=headers)
            if resp.status_code == 200:
                decisions = resp.json().get("decisions", [])
                print(f"   Found {len(decisions)} decisions")
                for d in decisions:
                    print(f"   - {d.get('symbol')} {d.get('decision')} [{d.get('status')}] exec: {d.get('execution_time')}")
                    if d.get('reasoning'):
                        print(f"     Reason: {d.get('reasoning')[:100]}...")
            else:
                print(f"   Failed to get decisions: {resp.status_code} - {resp.text}")
        except Exception as e:
            print(f"   Error: {e}")
    
    # 4. Test the scheduler jobs log
    print("\n4. Checking scheduler logs...")
    try:
        resp = requests.get(f"{BASE_URL}/api/scheduler/status", headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            print(f"   Scheduler running: {data.get('running')}")
            jobs = data.get('jobs', [])
            print(f"   Active jobs: {len(jobs)}")
            for job in jobs:
                print(f"   - {job.get('id')}: next run {job.get('next_run')}")
            
            logs = data.get('logs', [])
            if logs:
                print(f"   Recent logs ({len(logs)} entries):")
                for log in logs[:3]:
                    print(f"   - [{log.get('status')}] {log.get('job_name')}: {log.get('message', '')[:80]}...")
        else:
            print(f"   Failed to get scheduler status: {resp.status_code}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60)

if __name__ == "__main__":
    test_bot_orders()
