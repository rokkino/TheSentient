import requests
import json
import time

BASE_URL = 'http://localhost:8000'

# Login first - try with email
login_data = {'username': 'technosharing@gmail.com', 'password': 'password123'}
resp = requests.post(f'{BASE_URL}/api/auth/login', json=login_data)
if resp.status_code != 200:
    print(f'Login failed: {resp.text}')
    exit(1)
token = resp.json().get('access_token')
print(f'Logged in successfully')

headers = {'Authorization': f'Bearer {token}'}

# Deactivate bot first
print('Deactivating bot...')
resp = requests.post(f'{BASE_URL}/api/bot/1/deactivate', headers=headers)
print(f'Deactivate response: {resp.status_code}')

time.sleep(2)

# Activate bot again
print('Activating bot...')
resp = requests.post(f'{BASE_URL}/api/bot/1/activate', headers=headers)
print(f'Activate response: {resp.status_code}')
if resp.status_code == 200:
    print(f'Bot activated: {resp.json()}')
else:
    print(f'Error: {resp.text}')

time.sleep(5)  # Wait for async processing

# Check decisions
print()
print('Checking decisions...')
resp = requests.get(f'{BASE_URL}/api/bot/decisions?bot_id=1&limit=10', headers=headers)
if resp.status_code == 200:
    decisions = resp.json().get('decisions', [])
    print(f'Found {len(decisions)} decisions:')
    for d in decisions:
        sym = d.get('symbol', 'N/A')
        dec = d.get('decision', 'N/A')
        status = d.get('status', 'N/A')
        exec_time = d.get('execution_time', 'N/A')
        print(f'  - {sym} {dec} [{status}] exec: {exec_time}')
else:
    print(f'Error: {resp.text}')
