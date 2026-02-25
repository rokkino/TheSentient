"""
Chat Message Model
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from .user import Base

class Message(Base):
    __tablename__ = 'messages'
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    username = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String, default="text")  # "text" or "image"
    image_data = Column(Text, nullable=True)  # Base64 encoded image
    recipient_id = Column(Integer, ForeignKey('users.id'), nullable=True)  # For private messages
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationship to user (specify foreign_keys since we have multiple FKs to User)
    user = relationship("User", foreign_keys=[user_id], backref="messages")
