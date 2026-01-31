import json
import os
from datetime import datetime, timedelta

today = datetime.now().date()
tomorrow = today + timedelta(days=1)

print(f'Today: {today}')
print(f'Tomorrow: {tomorrow}')
print()

# Check for cached earnings
cache_dir = 'backend/memory/earnings'
if os.path.exists(cache_dir):
    files = os.listdir(cache_dir)
    print(f'Cached earnings files: {len(files)}')
    
    # Look for today and tomorrow
    today_file = f'earnings_{today}.json'
    tomorrow_file = f'earnings_{tomorrow}.json'
    
    for target_file in [today_file, tomorrow_file]:
        filepath = os.path.join(cache_dir, target_file)
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                data = json.load(f)
            earnings = data.get('data', [])
            print(f'{target_file}: {len(earnings)} earnings')
            # Show first 5
            for e in earnings[:5]:
                sym = e.get('symbol')
                comp = e.get('company', '')
                time_slot = e.get('time', 'TBD')
                print(f"  - {sym}: {comp[:30] if comp else sym} ({time_slot})")
        else:
            print(f'{target_file}: NOT FOUND')
else:
    print('Cache dir not found!')
