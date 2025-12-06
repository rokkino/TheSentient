"""
FastAPI Backend for The Sentient Portfolio Tracker
"""
from __future__ import annotations
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
import asyncio
from datetime import datetime
import json
import sys
import os
import shutil
import uuid
from pathlib import Path

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from services.market_data import MarketDataService
from services.news_service import NewsService
from services.watchlist_service import WatchlistService
from services.search_service import SearchService
from services.ai_service import AIService
from services.earnings_service import EarningsService
from services.auth_service import create_user, authenticate_user, create_access_token, get_user_by_id, verify_token, get_user_by_username, get_user_by_email
from services.chat_service import chat_service
# from services.alpaca_service import alpaca_service  # Will be imported when service is created
from websocket_manager import WebSocketManager
from models.user import init_db, get_db, User
from fastapi import Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

app = FastAPI(title="The Sentient API", version="1.0.0")

# Initialize database (non-blocking)
try:
    init_db()
    print("Database initialized successfully")
except Exception as e:
    print(f"Warning: Database initialization failed: {e}")
    print("The app will continue, but database operations may fail")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# CORS middleware for Vue.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite default ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create uploads directory if it doesn't exist
UPLOAD_DIR = Path("uploads/profile_pictures")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Serve uploaded files
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Initialize services
market_data_service = MarketDataService()
news_service = NewsService()
watchlist_service = WatchlistService()
search_service = SearchService()
ai_service = AIService()
earnings_service = EarningsService()
ws_manager = WebSocketManager()

# Pydantic models
class WatchlistItem(BaseModel):
    symbol: str
    name: str

class NewsItem(BaseModel):
    source: str
    ticker: str
    title: str
    link: str
    publisher: Optional[str] = None
    timestamp: datetime
    text: str
    trading_signal: Optional[Dict[str, Any]] = None

class ChartRequest(BaseModel):
    ticker: str
    timeframe: str
    chart_type: str = "candle"

class SearchRequest(BaseModel):
    query: str

class UserRegister(BaseModel):
    username: str
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    bio: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None

class ProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    bio: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    profile_picture_url: Optional[str] = None

class ChatMessage(BaseModel):
    message: str
    type: str = "text"  # "text" or "image"
    image_data: Optional[str] = None  # Base64 encoded image

class AlpacaOrderRequest(BaseModel):
    symbol: str
    qty: float
    side: str  # "buy" or "sell"
    order_type: str = "market"  # "market", "limit", "stop", "stop_limit"
    time_in_force: str = "day"  # "day", "gtc", "opg", "cls", "ioc", "fok"
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None

# API Routes
@app.get("/")
async def root():
    return {"message": "The Sentient API", "status": "running"}

@app.get("/api/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# Market Data Endpoints
@app.post("/api/chart")
async def get_chart(request: ChartRequest):
    """Get chart data for a ticker"""
    try:
        data = await market_data_service.get_chart_data(
            request.ticker,
            request.timeframe,
            request.chart_type
        )
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/quote/{ticker}")
async def get_quote(ticker: str, timeframe: str = "1d"):
    """Get current quote for a ticker with change calculated based on timeframe"""
    try:
        quote = await market_data_service.get_quote(ticker, timeframe)
        return quote
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Search Endpoints
@app.post("/api/search")
async def search(request: SearchRequest):
    """Search for assets"""
    try:
        results = await search_service.search(request.query)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Watchlist Endpoints
@app.get("/api/watchlist")
async def get_watchlist():
    """Get current watchlist"""
    return {"watchlist": watchlist_service.get_watchlist()}

@app.post("/api/watchlist")
async def add_to_watchlist(item: WatchlistItem):
    """Add item to watchlist"""
    print(f"API: Adding to watchlist: {item.symbol}, {item.name}")
    try:
        watchlist_service.add_item(item.symbol, item.name)
        print("API: Item added successfully")
        return {"message": "Item added", "watchlist": watchlist_service.get_watchlist()}
    except Exception as e:
        print(f"API: Error adding item: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/watchlist/{symbol}")
async def remove_from_watchlist(symbol: str):
    """Remove item from watchlist"""
    watchlist_service.remove_item(symbol)
    return {"message": "Item removed", "watchlist": watchlist_service.get_watchlist()}

# News Endpoints
@app.get("/api/news")
async def get_news(tickers: Optional[str] = None, limit: int = 50, publishers: Optional[str] = None):
    """Get news feed with optional publisher filtering"""
    try:
        print(f"News API called: tickers={tickers}, limit={limit}, publishers={publishers}")
        ticker_list = tickers.split(",") if tickers else None
        if ticker_list:
            ticker_list = [t.strip() for t in ticker_list if t.strip()]
        publisher_list = publishers.split(",") if publishers else None
        if publisher_list:
            publisher_list = [p.strip() for p in publisher_list if p.strip()]
        print(f"Processing news request: ticker_list={ticker_list}, limit={limit}, publisher_list={publisher_list}")
        news_items = await news_service.get_news(ticker_list, limit, publisher_list)
        print(f"Returning {len(news_items)} news items")
        return {"news": news_items}
    except Exception as e:
        import traceback
        print(f"Error in get_news endpoint: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/news/{ticker}")
async def get_ticker_news(ticker: str, limit: int = 20, publishers: Optional[str] = None):
    """Get news for specific ticker with optional publisher filtering"""
    try:
        publisher_list = publishers.split(",") if publishers else None
        if publisher_list:
            publisher_list = [p.strip() for p in publisher_list if p.strip()]
        news_items = await news_service.get_news([ticker], limit, publisher_list)
        return {"news": news_items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/news/publishers")
async def get_news_publishers():
    """Get list of all available news publishers"""
    try:
        # Get a sample of news to extract publishers
        sample_news = await news_service.get_news(None, 200)
        publishers = set()
        for item in sample_news:
            if item.get('publisher'):
                publishers.add(item['publisher'])
        return {"publishers": sorted(list(publishers))}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# AI Analysis Endpoints
@app.post("/api/analyze")
async def analyze_news(news_item: Dict[str, Any]):
    """Analyze news item with AI"""
    try:
        analysis = await ai_service.analyze_news(news_item)
        return {"analysis": analysis}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Earnings Endpoints
@app.get("/api/earnings")
async def get_earnings(start_date: Optional[str] = None, weeks: int = 1, offset: int = 0):
    """Get earnings calendar"""
    try:
        earnings = await earnings_service.get_earnings_calendar(start_date, weeks, offset)
        return {"earnings": earnings, "offset": offset, "weeks": weeks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/earnings/{ticker}")
async def get_ticker_earnings(ticker: str):
    """Get earnings for a specific ticker"""
    try:
        earnings = await earnings_service.get_ticker_earnings(ticker)
        if earnings:
            return {"earnings": earnings}
        else:
            raise HTTPException(status_code=404, detail="Earnings not found for this ticker")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Authentication Endpoints
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Get current authenticated user"""
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    user_id = payload.get("sub")
    user = get_user_by_id(db, int(user_id))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

@app.post("/api/auth/register")
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register a new user"""
    try:
        # Check if username or email already exists
        if get_user_by_username(db, user_data.username):
            raise HTTPException(status_code=400, detail="Username already registered")
        if get_user_by_email(db, user_data.email):
            raise HTTPException(status_code=400, detail="Email already registered")
        
        user = create_user(db, user_data.username, user_data.email, user_data.password)
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "message": "User created successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Registration error: {error_details}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@app.post("/api/auth/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login and get access token"""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    access_token = create_access_token(data={"sub": str(user.id)})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "bio": user.bio,
            "phone": user.phone,
            "location": user.location,
            "website": user.website,
            "profile_picture_url": user.profile_picture_url,
        }
    }

@app.get("/api/auth/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "bio": current_user.bio,
        "phone": current_user.phone,
        "location": current_user.location,
        "website": current_user.website,
        "profile_picture_url": current_user.profile_picture_url,
    }

@app.post("/api/auth/logout")
async def logout():
    """Logout (client-side token removal)"""
    return {"message": "Logged out successfully"}

@app.put("/api/auth/profile")
async def update_profile(profile_data: ProfileUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Update user profile"""
    try:
        if profile_data.first_name is not None:
            current_user.first_name = profile_data.first_name
        if profile_data.last_name is not None:
            current_user.last_name = profile_data.last_name
        if profile_data.bio is not None:
            current_user.bio = profile_data.bio
        if profile_data.phone is not None:
            current_user.phone = profile_data.phone
        if profile_data.location is not None:
            current_user.location = profile_data.location
        if profile_data.website is not None:
            current_user.website = profile_data.website
        if profile_data.profile_picture_url is not None:
            current_user.profile_picture_url = profile_data.profile_picture_url
        
        current_user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(current_user)
        
        return {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "first_name": current_user.first_name,
            "last_name": current_user.last_name,
            "bio": current_user.bio,
            "phone": current_user.phone,
            "location": current_user.location,
            "website": current_user.website,
            "profile_picture_url": current_user.profile_picture_url,
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auth/profile/picture")
async def upload_profile_picture(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload profile picture"""
    try:
        # Create uploads directory if it doesn't exist
        upload_dir = Path("uploads/profile_pictures")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        file_ext = Path(file.filename).suffix
        unique_filename = f"{current_user.id}_{uuid.uuid4()}{file_ext}"
        file_path = upload_dir / unique_filename
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Update user profile picture URL
        # In production, you'd upload to S3/cloud storage and get a URL
        # For now, we'll use a relative path
        profile_picture_url = f"/uploads/profile_pictures/{unique_filename}"
        current_user.profile_picture_url = profile_picture_url
        db.commit()
        db.refresh(current_user)
        
        return {
            "url": profile_picture_url,
            "message": "Profile picture uploaded successfully"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to upload profile picture: {str(e)}")

# Chat Endpoints
@app.get("/api/chat/messages")
async def get_chat_messages(limit: int = 100):
    """Get recent chat messages"""
    messages = chat_service.get_messages(limit)
    return {"messages": messages}

@app.post("/api/chat/message")
async def send_chat_message(message: ChatMessage, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Send a chat message"""
    try:
        chat_msg = chat_service.add_message(
            current_user.id,
            current_user.username,
            message.message,
            message.type,
            message.image_data
        )
        
        # Broadcast to all connected WebSocket clients
        await ws_manager.broadcast({
            "type": "chat_message",
            "data": chat_msg
        })
        
        return {"message": chat_msg}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auth/profile/picture")
async def upload_profile_picture(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload profile picture"""
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Validate file size (max 5MB)
        contents = await file.read()
        if len(contents) > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Image size must be less than 5MB")
        
        # Generate unique filename
        file_ext = Path(file.filename).suffix
        unique_filename = f"{current_user.id}_{uuid.uuid4()}{file_ext}"
        file_path = UPLOAD_DIR / unique_filename
        
        # Save file
        with open(file_path, "wb") as buffer:
            buffer.write(contents)
        
        # Generate URL (in production, use actual domain/CDN)
        file_url = f"/uploads/profile_pictures/{unique_filename}"
        
        # Update user profile
        db_gen = get_db()
        db = next(db_gen)
        try:
            current_user.profile_picture_url = file_url
            db.commit()
            db.refresh(current_user)
        finally:
            pass  # get_db() is a generator, we don't close it manually
        
        return {"url": file_url, "message": "Profile picture uploaded successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload image: {str(e)}")

# Alpaca Paper Trading API endpoints
@app.get("/api/alpaca/account")
async def get_alpaca_account(current_user: User = Depends(get_current_user)):
    """Get Alpaca account information"""
    try:
        account = await alpaca_service.get_account()
        return account
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/alpaca/positions")
async def get_alpaca_positions(current_user: User = Depends(get_current_user)):
    """Get all open positions"""
    try:
        positions = await alpaca_service.get_positions()
        return {"positions": positions}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/alpaca/orders")
async def get_alpaca_orders(
    status: Optional[str] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user)
):
    """Get orders"""
    try:
        orders = await alpaca_service.get_orders(status=status, limit=limit)
        return {"orders": orders}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/alpaca/orders")
async def place_alpaca_order(
    order_data: AlpacaOrderRequest,
    current_user: User = Depends(get_current_user)
):
    """Place an order"""
    try:
        order = await alpaca_service.place_order(
            symbol=order_data.symbol,
            qty=order_data.qty,
            side=order_data.side,
            order_type=order_data.order_type,
            time_in_force=order_data.time_in_force,
            limit_price=order_data.limit_price,
            stop_price=order_data.stop_price
        )
        return order
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/alpaca/orders/{order_id}")
async def cancel_alpaca_order(order_id: str, current_user: User = Depends(get_current_user)):
    """Cancel an order"""
    try:
        result = await alpaca_service.cancel_order(order_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/alpaca/orders")
async def cancel_all_alpaca_orders(current_user: User = Depends(get_current_user)):
    """Cancel all orders"""
    try:
        result = await alpaca_service.cancel_all_orders()
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/alpaca/portfolio/history")
async def get_alpaca_portfolio_history(
    period: str = "1M",
    timeframe: str = "1Day",
    current_user: User = Depends(get_current_user)
):
    """Get portfolio history"""
    try:
        history = await alpaca_service.get_portfolio_history(period=period, timeframe=timeframe)
        return history
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time news and chat updates"""
    await ws_manager.connect(websocket)
    try:
        # Start background tasks
        asyncio.create_task(news_service.start_news_monitor(ws_manager))
        
        while True:
            data = await websocket.receive_text()
            # Handle client messages if needed
            message = json.loads(data)
            if message.get("type") == "subscribe_news":
                await ws_manager.send_personal_message(
                    {"type": "subscribed", "tickers": message.get("tickers")},
                    websocket
                )
            elif message.get("type") == "chat_message":
                # Handle chat messages via WebSocket (alternative to REST)
                # For now, we use REST API for sending messages
                pass
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Hot reload for development
        log_level="info"
    )

