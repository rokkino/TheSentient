import sys
import os

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.web_search_service import web_search_service

def test_search():
    print("Testing WebSearchService...")
    query = "current price of Bitcoin"
    print(f"Searching for: {query}")
    results = web_search_service.search(query)
    print("Results:")
    print(results)
    
    if "No search results found" not in results and "Error" not in results:
        print("\nSUCCESS: Search returned results.")
    else:
        print("\nFAILURE: Search failed.")

if __name__ == "__main__":
    test_search()
