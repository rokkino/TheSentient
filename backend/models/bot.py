"""
Bot Model - Database models for trading bots
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Float
from sqlalchemy.orm import relationship
from models.user import Base
from datetime import datetime
import json

class Bot(Base):
    __tablename__ = 'bots'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    name = Column(String, nullable=False)
    bot_type = Column(String, nullable=False)  # e.g., 'earnings_report_genius'
    description = Column(Text, nullable=True)
    
    # Status
    status = Column(String, default='inactive')  # 'inactive', 'active', 'paused', 'error'
    is_active = Column(Boolean, default=False)
    
    # Configuration (stored as JSON)
    config = Column(Text, nullable=True)  # JSON string with API keys and settings
    
    # Activity Data (stored as JSON)
    activity_data = Column(Text, nullable=True)  # JSON string with real-time bot activity
    
    # Statistics
    win_rate = Column(Float, default=0.0)
    total_trades = Column(Integer, default=0)
    profit = Column(Float, default=0.0)  # Total profit percentage
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    activated_at = Column(DateTime, nullable=True)
    
    # Relationship
    user = relationship("User", backref="bots")
    
    def get_config(self) -> dict:
        """Get bot configuration as dictionary"""
        if self.config:
            try:
                return json.loads(self.config)
            except:
                return {}
        return {}
    
    def set_config(self, config_dict: dict):
        """Set bot configuration from dictionary"""
        self.config = json.dumps(config_dict)
    
    def is_configured(self) -> bool:
        """Check if bot has required configuration"""
        config = self.get_config()
        
        # For earnings_report_genius, we need broker credentials AND Gemini API key
        if self.bot_type == 'earnings_report_genius':
            gemini_configured = bool(config.get('gemini_api_key'))
            
            broker = config.get('broker', 'IG')  # Default to IG
            
            if broker == 'Alpaca':
                return bool(
                    gemini_configured and
                    config.get('alpaca_api_key') and
                    config.get('alpaca_api_secret')
                )
            else:  # IG Markets
                return bool(
                    gemini_configured and
                    config.get('ig_username') and 
                    config.get('ig_password') and 
                    config.get('ig_api_key')
                )
        
        return False
    
    def to_dict(self) -> dict:
        """Convert bot to dictionary"""
        # Get list of configured fields (keys in the config dict)
        config_keys = []
        if self.config:
            try:
                config_dict = json.loads(self.config)
                config_keys = list(config_dict.keys())
            except:
                pass

        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'bot_type': self.bot_type,
            'description': self.description,
            'status': self.status,
            'is_active': self.is_active,
            'is_configured': self.is_configured(),
            'configured_fields': config_keys,
            'win_rate': self.win_rate,
            'total_trades': self.total_trades,
            'profit': self.profit,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'activated_at': self.activated_at.isoformat() if self.activated_at else None,
            'activity_data': json.loads(self.activity_data) if self.activity_data else None,
        }


