#!/usr/bin/env python3
import asyncio
import sys
sys.path.append('src/backend/backend')
from services.earnings_service import EarningsService

async def main():
    service = EarningsService()
    print("Fetching earnings calendar...")
    earnings = await service.get_earnings_calendar(months=1, use_cache=True)
    print(f"Total earnings: {len(earnings)}")
    
    # Filter for today and tomorrow
    from datetime import datetime, date, timedelta
    today = date.today()
    tomorrow = today + timedelta(days=1)
    
    print(f"\nToday: {today}, Tomorrow: {tomorrow}")
    
    for e in earnings[:50]:  # show first 50
        date_str = e.get('date', '')
        if 'T' in date_str:
            date_str = date_str.split('T')[0]
        try:
            e_date = datetime.fromisoformat(date_str).date()
        except:
            continue
        if e_date in (today, tomorrow):
            symbol = e.get('symbol', 'N/A')
            time = e.get('time', 'TBD')
            eps_estimate = e.get('epsEstimate', 'N/A')
            print(f"{symbol}: {e_date} {time} EPS: {eps_estimate}")
    
    # Count
    count_today = sum(1 for e in earnings if 'date' in e and str(today) in e['date'])
    count_tomorrow = sum(1 for e in earnings if 'date' in e and str(tomorrow) in e['date'])
    print(f"\nEarnings today: {count_today}, tomorrow: {count_tomorrow}")

if __name__ == "__main__":
    asyncio.run(main())