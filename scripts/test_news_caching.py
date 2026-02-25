import asyncio
import sys
import os
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from src.backend.services.news_service import NewsService
from src.backend.models.news import News
from src.backend.models.user import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Setup in-memory DB
engine = create_engine('sqlite:///:memory:')
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)

async def test_news_caching():
    print("Starting News Caching Verification...")
    
    db = SessionLocal()
    service = NewsService()
    
    # Mock data
    mock_news_data = [
        {
            'title': 'Test News 1',
            'link': 'http://test.com/1',
            'publisher': 'Test Pub',
            'providerPublishTime': datetime.now().timestamp(),
            'thumbnail': {'resolutions': [{'url': 'http://img.com/1'}]}
        }
    ]
    
    # 1. Test Fetch and Cache
    print("\n1. Testing Fetch and Cache...")
    with patch('yfinance.Ticker') as mock_ticker:
        mock_instance = MagicMock()
        mock_instance.news = mock_news_data
        mock_ticker.return_value = mock_instance
        
        # Fetch news
        news = await service.get_news(['AAPL'], limit=10, db=db)
        print(f"Fetched {len(news)} items")
        
        # Verify DB
        db_news = db.query(News).all()
        print(f"DB contains {len(db_news)} items")
        assert len(db_news) == 1
        assert db_news[0].title == 'Test News 1'
        print("✅ Data saved to DB correctly")

    # 2. Test Cache Retrieval
    print("\n2. Testing Cache Retrieval...")
    # Clear in-memory list to ensure we rely on DB/Mock
    # Mock yfinance to return EMPTY list, so we MUST get data from DB if caching works
    with patch('yfinance.Ticker') as mock_ticker:
        mock_instance = MagicMock()
        mock_instance.news = [] # Return nothing new
        mock_ticker.return_value = mock_instance
        
        news = await service.get_news(['AAPL'], limit=10, db=db)
        print(f"Fetched {len(news)} items (should be from cache)")
        
        assert len(news) == 1
        assert news[0]['title'] == 'Test News 1'
        print("✅ Data retrieved from DB correctly")

    # 3. Test Cleanup
    print("\n3. Testing Cleanup...")
    # Insert old news
    old_date = datetime.utcnow() - timedelta(days=8)
    old_news = News(
        ticker='AAPL',
        title='Old News',
        link='http://test.com/old',
        publisher='Old Pub',
        timestamp=old_date,
        content='Old content'
    )
    db.add(old_news)
    db.commit()
    
    print(f"Added old news item from {old_date}")
    count_before = db.query(News).count()
    print(f"DB count before cleanup: {count_before}")
    
    # Trigger cleanup via get_news (mocking new data to trigger save/cleanup)
    with patch('yfinance.Ticker') as mock_ticker:
        mock_instance = MagicMock()
        mock_instance.news = mock_news_data # Return same data to trigger "save" logic which calls cleanup
        mock_ticker.return_value = mock_instance
        
        await service.get_news(['AAPL'], limit=10, db=db)
        
    count_after = db.query(News).count()
    print(f"DB count after cleanup: {count_after}")
    
    # Should have 1 item (the fresh one), old one removed
    # Note: The fresh one is 'Test News 1' which is already there, so count should be 1
    assert count_after == 1
    remaining = db.query(News).first()
    assert remaining.title == 'Test News 1'
    print("✅ Old news cleaned up correctly")

    print("\n🎉 All verification steps passed!")

if __name__ == "__main__":
    asyncio.run(test_news_caching())
