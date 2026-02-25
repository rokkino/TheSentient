import requests
r = requests.get('http://localhost:8001/api/bots')
print("Status:", r.status_code)
data = r.json()
print("First bot keys:", data[0].keys() if data else "No bots")
for bot in data:
    print(f"Bot {bot['id']} - win_rate: {bot.get('win_rate')}, profit: {bot.get('profit')}")
    hist = bot.get('performance_history')
    if hist:
        print(f"  History pts: {len(hist)}")
    else:
        print("  History: None")
