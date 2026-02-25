#!/usr/bin/env python3
import sys
import os
import asyncio
from datetime import datetime, date, timedelta

BACKEND_DIR = os.path.join(os.getcwd(), "src", "backend", "backend")
sys.path.insert(0, BACKEND_DIR)

async def test_earnings():
    from services.earnings_service import earnings_service
    
    print(f"Current date: {datetime.now().date()}")
    print(f"Testing earnings calendar with default parameters...")
    
    # Test with no start_date (should default to today)
    earnings = await earnings_service.get_earnings_calendar(
        start_date=None,
        months=6,
        offset_months=0,
        use_cache=True
    )
    
    print(f"Total earnings returned: {len(earnings)}")
    if earnings:
        # Find earliest and latest dates
        dates = []
        for e in earnings:
            if 'date' in e:
                dates.append(e['date'])
            elif 'reportDate' in e:
                dates.append(e['reportDate'])
        if dates:
            print(f"Earliest date: {min(dates)}")
            print(f"Latest date: {max(dates)}")
        # Print first few
        for i, e in enumerate(earnings[:5]):
            print(f"  {i+1}. {e.get('symbol', 'N/A')} - {e.get('date', 'N/A')} - {e.get('companyName', 'N/A')}")
    
    # Check cache directory
    cache_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src', 'backend', 'backend', 'memory', 'earnings')
    if os.path.exists(cache_dir):
        print(f"\nCache directory: {cache_dir}")
        files = os.listdir(cache_dir)
        print(f"Cache files: {len(files)}")
        for f in sorted(files)[:10]:
            print(f"  {f}")
    else:
        print(f"\nCache directory not found: {cache_dir}")
    
    # Test with explicit start_date = today
    today = datetime.now().date().isoformat()
    print(f"\nTesting with start_date={today}")
    earnings2 = await earnings_service.get_earnings_calendar(
        start_date=today,
        months=1,
        offset_months=0,
        use_cache=False  # bypass cache
    )
    print(f"Earnings with cache bypass: {len(earnings2)}")
    if earnings2:
        for e in earnings2[:3]:
            print(f"  {e.get('symbol', 'N/A')} - {e.get('date', 'N/A')}")

if __name__ == "__main__":
    asyncio.run(test_earnings())