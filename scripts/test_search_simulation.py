import asyncio
import sys
import os

# Add backend directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from src.backend.services.symbol_mapper import symbol_mapper

async def test_search_simulation():
    # Simulate main.py logic where alpaca_service EXISTS but is not configured
    # In main.py, it would skip the first check, skip the is_configured() check,
    # skip the user account check, and reach the bottom.
    
    query = "nvidia"
    
    print("START_SIMULATION_FULL")
    
    # Simulate the flow falling through to the end
    results = symbol_mapper.search(query)
    
    # Check results
    nvidia_found = any(r['symbol'] == 'NVDA' for r in results)
    
    if nvidia_found:
        print("SIMULATION_PASS: Found NVDA using symbol_mapper fallback")
    else:
        print(f"SIMULATION_FAIL: {len(results)} results found")
        for r in results:
            print(r)
            
    print("END_SIMULATION_FULL")

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(test_search_simulation())
