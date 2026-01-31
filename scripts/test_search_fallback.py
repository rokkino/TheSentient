import asyncio
import sys
import os

# Add backend directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from services.alpaca_service import alpaca_service

async def test_search():
    print("START_TEST")
    
    # Test 1: Search for NVIDIA
    results = await alpaca_service.search_assets("nvidia")
    nvidia_found = any(r['symbol'] == 'NVDA' for r in results)
    
    if nvidia_found:
        print("TEST_1_PASS: Found NVDA")
    else:
        print(f"TEST_1_FAIL: Found {len(results)} results")

    # Test 2: Search for GOOG
    results = await alpaca_service.search_assets("GOOG")
    if len(results) > 0:
        print("TEST_2_PASS: Found GOOG matches")
    else:
        print("TEST_2_FAIL: No results for GOOG")

    print("END_TEST")

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(test_search())
