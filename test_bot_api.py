"""
Simple script to check if the earnings bot can be activated and test a position
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_bot():
    print("=== Testing Earnings Bot via API ===\n")
    
    # 1. Check if we can get bots
    try:
        response = requests.get(f"{BASE_URL}/bots")
        if response.status_code == 200:
            bots = response.json()
            print(f"✅ Found {len(bots)} bot(s)")
            for bot in bots:
                print(f"\nBot: {bot.get('name')}")
                print(f"  ID: {bot.get('id')}")
                print(f"  Type: {bot.get('bot_type')}")
                print(f"  Status: {bot.get('status')}")
                print(f"  Active: {bot.get('is_active')}")
                
                # Try to activate if not active
                if not bot.get('is_active'):
                    print(f"\n  Attempting to activate bot {bot.get('id')}...")
                    activate_response = requests.post(f"{BASE_URL}/bots/{bot.get('id')}/activate")
                    if activate_response.status_code == 200:
                        print(f"  ✅ Bot activated successfully!")
                    else:
                        print(f"  ❌ Failed to activate: {activate_response.text}")
                else:
                    print(f"  ✅ Bot is already active")
        else:
            print(f"❌ Failed to get bots: {response.status_code}")
            print(response.text)
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # 2. Check earnings
    print("\n=== Checking Earnings ===")
    try:
        response = requests.get(f"{BASE_URL}/earnings/today-tomorrow")
        if response.status_code == 200:
            earnings = response.json()
            print(f"✅ Found {len(earnings)} earnings today/tomorrow")
            for e in earnings[:5]:
                print(f"  {e.get('symbol')} - {e.get('company')} at {e.get('time')}")
        else:
            print(f"❌ Failed to get earnings: {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting earnings: {e}")

if __name__ == "__main__":
    test_bot()
