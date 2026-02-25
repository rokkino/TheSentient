import asyncio
import sys
import os
from unittest.mock import MagicMock, patch

# Add backend directory to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from src.backend.services.chat_service import ChatService
from src.backend.models.user import User
from src.backend.models.bot import Bot

async def test_chat_search():
    print("Testing Chat Search Functionality...")
    
    # Mock dependencies
    mock_db = MagicMock()
    mock_user = User(id=1, username="testuser", bio="Test Bio")
    mock_db.query.return_value.filter.return_value.first.return_value = mock_user
    
    chat_service = ChatService()
    
    # Mock add_message to verify it's called
    chat_service.add_message = MagicMock()
    
    # Mock web_search_service
    with patch('services.web_search_service.web_search_service') as mock_search_service:
        mock_search_service.search.return_value = "Mock Search Results"
        
        # Test Case 1: Search Request
        print("\nTest Case 1: Search Request")
        await chat_service.process_ai_response(
            user_id=1,
            message="apple stock",
            db=mock_db,
            invite_llama=False,
            is_search=True
        )
        
        # Verify search was called
        mock_search_service.search.assert_called_with("apple stock")
        print("✅ Web search service called correctly")
        
        # Verify message was added
        chat_service.add_message.assert_called_with(
            db=mock_db,
            user_id=1,
            username="System Search",
            message="Mock Search Results",
            message_type="text"
        )
        print("✅ Search results added to chat")

        # Test Case 2: Normal Chat (No Search)
        print("\nTest Case 2: Normal Chat (No Search)")
        chat_service.add_message.reset_mock()
        mock_search_service.search.reset_mock()
        
        await chat_service.process_ai_response(
            user_id=1,
            message="hello",
            db=mock_db,
            invite_llama=False,
            is_search=False
        )
        
        # Verify search was NOT called
        mock_search_service.search.assert_not_called()
        print("✅ Web search service NOT called for normal chat")

if __name__ == "__main__":
    asyncio.run(test_chat_search())
