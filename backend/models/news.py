"""
News Model - Database model for storing news items
"""
from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime, timezone
from .user import Base

class News(Base):
    __tablename__ = 'news'
    
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True)
    title = Column(String)
    link = Column(String, unique=True, index=True)
    publisher = Column(String)
    timestamp = Column(DateTime, index=True)
    content = Column(Text, nullable=True)  # Summary or full text
    thumbnail_url = Column(String, nullable=True)
    sentiment = Column(String, nullable=True)  # 'positive', 'negative', 'neutral'
    extracted_assets = Column(Text, nullable=True)  # JSON array of assets mentioned
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
