"""
Chat Service - Handles group chat messages
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from models.user import User
from models.bot import Bot
from models.chat import Message
import uuid
from services.llama_service import llama_service
from services.gemini_service import GeminiService
import os

class ChatService:
    def __init__(self):
        pass
    
    def add_message(self, db: Session, user_id: int, username: str, message: str, message_type: str = "text", image_data: Optional[str] = None, recipient_id: Optional[int] = None) -> Dict[str, Any]:
        """Add a message to the chat database"""
        message_id = str(uuid.uuid4())
        
        new_message = Message(
            id=message_id,
            user_id=user_id,
            username=username,
            message=message,
            type=message_type,
            image_data=image_data,
            recipient_id=recipient_id,
            timestamp=datetime.utcnow()
        )
        
        db.add(new_message)
        db.commit()
        db.refresh(new_message)
        
        # Get user profile picture
        user = db.query(User).filter(User.id == user_id).first()
        profile_picture_url = user.profile_picture_url if user else None

        return {
            "id": new_message.id,
            "user_id": new_message.user_id,
            "username": new_message.username,
            "message": new_message.message,
            "type": new_message.type,
            "image_data": new_message.image_data,
            "recipient_id": new_message.recipient_id,
            "timestamp": new_message.timestamp.isoformat(),
            "profile_picture_url": profile_picture_url
        }

    def delete_message(self, db: Session, message_id: str) -> bool:
        """Delete a message by ID"""
        message = db.query(Message).filter(Message.id == message_id).first()
        if message:
            db.delete(message)
            db.commit()
            return True
        return False

    def clear_history(self, db: Session, user_id: int, recipient_id: Optional[int] = None) -> int:
        """Clear chat history for a user (private or public)"""
        try:
            query = db.query(Message)
            
            if recipient_id:
                # Private chat: delete messages between user_id and recipient_id
                from sqlalchemy import or_, and_
                query = query.filter(
                    or_(
                        and_(Message.user_id == user_id, Message.recipient_id == recipient_id),
                        and_(Message.user_id == recipient_id, Message.recipient_id == user_id)
                    )
                )
            else:
                # Public chat: delete all public messages (admin/cleanup function)
                # Or maybe just messages from this user?
                # For "Clear History" button usually implies clearing the view.
                # Since this is a shared public chat, deleting ALL messages might be too aggressive for one user.
                # But if the user wants to "remove entire history", they probably mean "delete everything I see".
                # Given this is likely a personal project or small team, deleting all public messages is acceptable.
                query = query.filter(Message.recipient_id == None)
            
            deleted_count = query.delete(synchronize_session=False)
            db.commit()
            return deleted_count
        except Exception as e:
            print(f"[ChatService] Error clearing history: {e}")
            db.rollback()
            return 0

    async def process_ai_response(self, user_id: int, message: str, db: Session, invite_llama: bool = False, invite_gemini: bool = False, is_search: bool = False, ws_manager = None):
        """Process message and generate AI response if enabled"""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            
            # Handle Web Search Request
            if is_search:
                print(f"[ChatService] Performing web search for user {user.username}: {message}")
                from services.web_search_service import web_search_service
                search_results = web_search_service.search(message)
                
                # Add Search Results to chat
                search_msg = self.add_message(
                    db=db,
                    user_id=1,  # System/AI user ID
                    username="System Search",
                    message=search_results,
                    message_type="text"
                )
                
                # Broadcast if ws_manager provided
                if ws_manager:
                    await ws_manager.broadcast({
                        "type": "chat_message",
                        "data": search_msg
                    })
                return

            # Only respond if invite_llama is True OR (legacy behavior) user has use_local_llama enabled AND it's a public chat (no recipient)
            # But user request says "normally is disable", so we should prioritize the invite_llama flag for this new feature.
            # Let's say: if invite_llama is True, we respond.
            if user and invite_llama:
                print(f"[ChatService] Generating Llama response for user {user.username}")
                
                # Build context from user profile and bots
                context_parts = []
                
                # User Profile Context
                context_parts.append(f"User Profile for {user.username}:")
                if user.bio:
                    context_parts.append(f"- Bio/Motto: {user.bio}")
                if user.location:
                    context_parts.append(f"- Location: {user.location}")
                if user.website:
                    context_parts.append(f"- Website: {user.website}")
                
                # Bots Context
                user_bots = db.query(Bot).filter(Bot.user_id == user_id).all()
                if user_bots:
                    context_parts.append("\nUser's Trading Bots:")
                    for bot in user_bots:
                        status_str = "Active" if bot.is_active else "Inactive"
                        context_parts.append(f"- Bot '{bot.name}' ({bot.bot_type}): Status={status_str}, Profit={bot.profit}%, Win Rate={bot.win_rate}%")
                else:
                    context_parts.append("\nUser has no trading bots configured yet.")
                
                context_str = "\n".join(context_parts)
                
                response_text = llama_service.generate_response(message, context=context_str, user_id=user_id)
                
                # Add AI response to chat
                ai_msg = self.add_message(
                    db=db,
                    user_id=-1,  # Llama AI user ID (matches frontend)
                    username="Llama AI",
                    message=response_text,
                    message_type="text"
                )
                
                # Broadcast if ws_manager provided
                if ws_manager:
                    await ws_manager.broadcast({
                        "type": "chat_message",
                        "data": ai_msg
                    })
            
            # Handle Gemini Response
            if user and invite_gemini:
                print(f"[ChatService] Generating Gemini response for user {user.username}")
                
                # Build context (reuse same context as Llama for now)
                context_parts = []
                context_parts.append(f"User Profile for {user.username}:")
                if user.bio:
                    context_parts.append(f"- Bio/Motto: {user.bio}")
                if user.location:
                    context_parts.append(f"- Location: {user.location}")
                if user.website:
                    context_parts.append(f"- Website: {user.website}")
                
                # Bots Context
                user_bots = db.query(Bot).filter(Bot.user_id == user_id).all()
                if user_bots:
                    context_parts.append("\nUser's Trading Bots:")
                    for bot in user_bots:
                        status_str = "Active" if bot.is_active else "Inactive"
                        context_parts.append(f"- Bot '{bot.name}' ({bot.bot_type}): Status={status_str}, Profit={bot.profit}%, Win Rate={bot.win_rate}%")
                else:
                    context_parts.append("\nUser has no trading bots configured yet.")
                
                context_str = "\n".join(context_parts)
                
                # Instantiate GeminiService
                gemini_api_key = user.gemini_api_key or os.getenv('GOOGLE_GEMINI_API_KEY')
                gemini_service = GeminiService(api_key=gemini_api_key)
                
                response_text = gemini_service.generate_response(message, context=context_str, user_id=user_id)
                
                # Add AI response to chat
                ai_msg = self.add_message(
                    db=db,
                    user_id=-2,  # Gemini AI user ID (matches frontend)
                    username="Gemini AI",
                    message=response_text,
                    message_type="text"
                )
                
                # Broadcast if ws_manager provided
                if ws_manager:
                    await ws_manager.broadcast({
                        "type": "chat_message",
                        "data": ai_msg
                    })
        except Exception as e:
            print(f"[ChatService] Error processing AI response: {e}")
    
    def get_messages(self, db: Session, limit: int = 100, user_id: Optional[int] = None, recipient_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get recent messages from database"""
        query = db.query(Message)
        
        if recipient_id:
            # Private chat: messages between user_id and recipient_id
            # (user -> recipient) OR (recipient -> user)
            from sqlalchemy import or_, and_
            query = query.filter(
                or_(
                    and_(Message.user_id == user_id, Message.recipient_id == recipient_id),
                    and_(Message.user_id == recipient_id, Message.recipient_id == user_id)
                )
            )
        else:
            # Public chat: messages with no recipient
            query = query.filter(Message.recipient_id == None)
            
        messages = query.order_by(Message.timestamp.desc()).limit(limit).all()
        
        # Convert to list of dicts and reverse to show oldest first (chat order)
        result = []
        for msg in messages:
            # Fetch user profile picture if available
            user = db.query(User).filter(User.id == msg.user_id).first()
            profile_picture_url = user.profile_picture_url if user else None
            
            result.append({
                "id": msg.id,
                "user_id": msg.user_id,
                "username": msg.username,
                "message": msg.message,
                "type": msg.type,
                "image_data": msg.image_data,
                "recipient_id": msg.recipient_id,
                "timestamp": msg.timestamp.isoformat(),
                "profile_picture_url": profile_picture_url
            })
        
        return result[::-1]
    
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

