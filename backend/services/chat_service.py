"""
Chat Service - Handles group chat messages
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from models.user import User
import base64
import os
import uuid

class ChatService:
    def __init__(self):
        self.messages: List[Dict[str, Any]] = []
        self.max_messages = 1000  # Keep last 1000 messages in memory
    
    def add_message(self, user_id: int, username: str, message: str, message_type: str = "text", image_data: Optional[str] = None) -> Dict[str, Any]:
        """Add a message to the chat"""
        chat_message = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "username": username,
            "message": message,
            "type": message_type,  # "text" or "image"
            "image_data": image_data,  # Base64 encoded image
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        self.messages.append(chat_message)
        
        # Keep only last max_messages
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
        
        return chat_message
    
    def get_messages(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent messages"""
        return self.messages[-limit:]
    
    def get_user_info(self, db: Session, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user information for display"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
        }

chat_service = ChatService()

