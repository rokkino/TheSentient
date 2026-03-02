import json
import asyncio
from src.backend.backend.services.news_service import NewsService

async def test():
    service = NewsService()
    news_item = {
        "title": "BofA initiates Eikon Therapeutics stock with buy rating on platform potential",
        "text": "BofA initiates Eikon Therapeutics stock with buy rating on platform potential"
    }
    result = service._simple_sentiment_analysis(news_item)
    print("Test 1 Result:", json.dumps(result, indent=2))
    
    news_item2 = {
        "title": "AAPL and MSFT are doing great today",
        "text": "The CEO of AAPL said MSFT is a good partner. Also mentioned TSLA and BTC."
    }
    result2 = service._simple_sentiment_analysis(news_item2)
    print("Test 2 Result:", json.dumps(result2, indent=2))

if __name__ == "__main__":
    asyncio.run(test())
