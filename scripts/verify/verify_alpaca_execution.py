import asyncio
import os
import sys
from datetime import datetime

# Setup path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from src.backend.models.user import SessionLocal, User
from src.backend.models.bot import Bot, Decision
from src.backend.models.account import Account
from src.backend.services.bot_service import bot_service
from src.backend.services.market_data import MarketDataService
from src.backend.services.symbol_mapper import symbol_mapper

async def test_execution():
    print("--- Starting Alpaca Execution Verification ---")
    
    db = SessionLocal()
    try:
        # 1. Identify or Create a Test Bot
        bot = db.query(Bot).first()
        if not bot:
            print("No bot found. Creating test bot...")
            # Ensure user exists
            user_id = 1
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                user = User(username="testuser", email="test@example.com", hashed_password="pw")
                db.add(user)
                db.commit()
                db.refresh(user)
                user_id = user.id
            
            # Create Bot
            bot = Bot(user_id=user_id, name="AlpacaTestBot", bot_type="Earnings", status="active", is_active=True)
            # Find Alpaca Account to link? Or just use config
            # Let's use legacy config for simplicity in test
            import os
            key = os.getenv("ALPACA_API_KEY")
            secret = os.getenv("ALPACA_API_SECRET")
            if key:
                 bot.config = f'{{"broker": "Alpaca", "alpaca_api_key": "{key}", "alpaca_api_secret": "{secret}", "alpaca_paper": true}}'
            else:
                 # Use dummy keys for verification if not provided
                 print("WARNING: Using dummy keys for verification")
                 bot.config = '{"broker": "Alpaca", "alpaca_api_key": "PK_TEST_DUMMY", "alpaca_api_secret": "SK_TEST_DUMMY", "alpaca_paper": true}'
                 
            db.add(bot)
            db.commit()
            db.refresh(bot)
            print(f"Created Bot: {bot.name}")

        print(f"Using Bot: {bot.name} (ID: {bot.id})")
        
        # 2. Check Service Configuration
        service = bot_service._get_configured_service(db, bot)
        if not service:
            print("Bot has no trading service configured. Attempting to configure Alpaca defaults if env vars exist.")
            # Verify env vars
            import os
            key = os.getenv("ALPACA_API_KEY")
            secret = os.getenv("ALPACA_API_SECRET")
            if key and secret:
                from src.backend.services.alpaca_service import AlpacaService
                service = AlpacaService(api_key=key, api_secret=secret, paper=True)
                print("Created temporary AlpacaService from env vars.")
            else:
                print("FAIL: No Alpaca Configuration found in Bot or Env Vars.")
                return
        
        print(f"Service Configured: {type(service).__name__}")
        
        # 3. Create a Test Decision
        symbol = "AAPL"
        decision = Decision(
            bot_id=bot.id,
            symbol=symbol,
            decision="BUY",
            status="PENDING",
            execution_time=datetime.now(),
            reasoning="Verification Test Order"
        )
        db.add(decision)
        db.commit()
        db.refresh(decision)
        print(f"Created Test Decision: {decision.id} {decision.decision} {decision.symbol}")
        
        # 4. Simulate Execution Logic (from main.py and scheduler_jobs.py)
        try:
            from src.backend.services.alpaca_service import AlpacaService
            
            # Normalize
            norm_symbol = symbol_mapper.normalize_symbol(symbol)
            
            # Price & Qty
            market_data_service = MarketDataService()
            current_price = 0.0
            ORDER_AMOUNT_USD = 1000.0
            qty = 1.0
            
            try:
                # We need to await this
                quote = await market_data_service.get_quote(norm_symbol)
                current_price = quote.get('price', 0.0)
                print(f"Current Price for {norm_symbol}: ${current_price}")
            except Exception as e:
                print(f"Error fetching price: {e}")
            
            if current_price > 0:
                qty = round(ORDER_AMOUNT_USD / current_price, 4)
                if qty < 0.0001: qty = 0.0001
            
            print(f"Executing Order: {norm_symbol} Qty: {qty} (Target ${ORDER_AMOUNT_USD})")
            
            # Place Order
            # CAUTION: This places a real paper order
            if isinstance(service, AlpacaService):
                result = await service.place_market_order(
                    symbol=norm_symbol, 
                    qty=qty, 
                    side="buy"
                )
                print("Order Placed Successfully!")
                print(f"Order ID: {result.get('id')}")
                print(f"Status: {result.get('status')}")
                
                # Update Decision
                decision.status = "EXECUTED"
                decision.reasoning += f" | VERIFIED EXECUTION ID: {result.get('id')}"
                db.commit()
                
            else:
                print(f"Skipping actual execution: Service is {type(service)}, expected AlpacaService")
                
        except Exception as e:
            print(f"Execution Failed: {e}")
            import traceback
            traceback.print_exc()
            
    finally:
        db.close()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_execution())
