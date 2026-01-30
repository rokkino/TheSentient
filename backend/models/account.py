
"""
Account Model - Database models for external platform accounts (IG, Alpaca, eToro, etc.)
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from models.user import Base
from datetime import datetime
import json

class Account(Base):
    __tablename__ = 'accounts'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    platform = Column(String, nullable=False)  # 'IG', 'Alpaca', 'eToro', 'Binance', etc.
    name = Column(String, nullable=False)      # Friendly name e.g. "My IG Real", "Paper Account"
    
    # Store credentials as JSON string
    # In a real production app, these should be encrypted. 
    # For this local assistant, we'll store them as JSON text for simplicity but marked as sensitive.
    credentials = Column(Text, nullable=False) 
    
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False) # If true, this is the default account for this platform
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    user = relationship("User", backref="accounts")
    
    def set_credentials(self, creds_dict: dict):
        self.credentials = json.dumps(creds_dict)
        
    def get_credentials(self) -> dict:
        try:
            return json.loads(self.credentials)
        except:
            return {}
            
    def to_dict(self, include_credentials=False) -> dict:
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'platform': self.platform,
            'name': self.name,
            'is_active': self.is_active,
            'is_default': self.is_default,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_credentials:
            data['credentials'] = self.get_credentials()
            
        return data
