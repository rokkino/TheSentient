"""
Bot Service - Handles bot management, configuration, and execution
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from models.bot import Bot
from models.user import User
from datetime import datetime, date, timedelta
import asyncio
import os

class BotService:
    def __init__(self):
        self.active_bots: Dict[int, Any] = {}  # Track active bots by bot_id
    
    def create_bot(self, db: Session, user_id: int, name: str, bot_type: str, description: Optional[str] = None) -> Bot:
        """Create a new bot"""
        try:
            print(f"[BotService] Creating bot: user_id={user_id}, name={name}, type={bot_type}")
            bot = Bot(
                user_id=user_id,
                name=name,
                bot_type=bot_type,
                description=description,
                status='inactive',
                is_active=False
            )
            db.add(bot)
            db.commit()
            db.refresh(bot)
            print(f"[BotService] Bot created successfully: id={bot.id}, name={bot.name}, user_id={bot.user_id}")
            return bot
        except Exception as e:
            print(f"[BotService] Error creating bot: {e}")
            db.rollback()
            import traceback
            traceback.print_exc()
            raise
    
    def get_bot(self, db: Session, bot_id: int, user_id: Optional[int] = None) -> Optional[Bot]:
        """Get a bot by ID, optionally filtered by user_id"""
        query = db.query(Bot).filter(Bot.id == bot_id)
        if user_id:
            query = query.filter(Bot.user_id == user_id)
        return query.first()
    
    def get_bot_by_name(self, db: Session, user_id: int, name: str) -> Optional[Bot]:
        """Get a bot by name for a specific user"""
        return db.query(Bot).filter(Bot.user_id == user_id, Bot.name == name).first()

    
    def get_user_bots(self, db: Session, user_id: int) -> List[Bot]:
        """Get all bots for a user"""
        try:
            bots = db.query(Bot).filter(Bot.user_id == user_id).order_by(Bot.created_at.desc()).all()
            print(f"[BotService] Found {len(bots)} bots for user {user_id}")
            for bot in bots:
                print(f"[BotService] Bot: id={bot.id}, name={bot.name}, user_id={bot.user_id}")
            return bots
        except Exception as e:
            print(f"[BotService] Error getting bots: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_all_bots(self, db: Session) -> List[Bot]:
        """Get all bots (for competition/public view)"""
        return db.query(Bot).filter(Bot.is_active == True).order_by(Bot.created_at.desc()).all()
    
    def update_bot_config(self, db: Session, bot_id: int, user_id: int, config: Dict[str, Any]) -> Bot:
        """Update bot configuration"""
        bot = self.get_bot(db, bot_id, user_id)
        if not bot:
            raise ValueError("Bot not found")
        
        bot.set_config(config)
        bot.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(bot)
        return bot
    
    def activate_bot(self, db: Session, bot_id: int, user_id: int) -> Bot:
        """Activate a bot (only if configured)"""
        bot = self.get_bot(db, bot_id, user_id)
        if not bot:
            raise ValueError("Bot not found")
        
        if not bot.is_configured():
            raise ValueError("Bot must be configured before activation")
        
        bot.is_active = True
        bot.status = 'active'
        bot.activated_at = datetime.utcnow()
        bot.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(bot)
        
        # Start bot execution (async)
        asyncio.create_task(self._start_bot(bot))
        
        return bot
    
    def deactivate_bot(self, db: Session, bot_id: int, user_id: int) -> Bot:
        """Deactivate a bot"""
        bot = self.get_bot(db, bot_id, user_id)
        if not bot:
            raise ValueError("Bot not found")
        
        bot.is_active = False
        bot.status = 'inactive'
        bot.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(bot)
        
        # Stop bot execution
        if bot_id in self.active_bots:
            del self.active_bots[bot_id]
        
        return bot
    
    def delete_bot(self, db: Session, bot_id: int, user_id: int) -> bool:
        """Delete a bot"""
        bot = self.get_bot(db, bot_id, user_id)
        if not bot:
            return False
        
        # Stop bot if active
        if bot.is_active:
            self.deactivate_bot(db, bot_id, user_id)
        
        db.delete(bot)
        db.commit()
        db.delete(bot)
        db.commit()
        return True
    
    def _log_activity(self, bot_id: int, message: str):
        """Log bot activity to file"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{timestamp}] [Bot {bot_id}] {message}\n"
            
            file_path = os.path.join("backend", "bot_activity.log")
            with open(file_path, "a") as f:
                f.write(log_entry)
        except Exception as e:
            print(f"Error logging activity: {e}")
    
    async def _start_bot(self, bot: Bot):
        """Start bot execution based on bot type"""
        if bot.bot_type == 'earnings_report_genius':
            await self._start_earnings_report_genius(bot)
        # Add more bot types here
    
    async def _start_earnings_report_genius(self, bot: Bot):
        """Start Earnings Report Genius bot"""
        from services.earnings_service import EarningsService
        from services.ig_service import IGMarketsService
        
        config = bot.get_config()
        earnings_service = EarningsService()
        
        # Get IG Markets credentials from bot config (required, no defaults)
        ig_username = config.get('ig_username')
        ig_password = config.get('ig_password')
        ig_api_key = config.get('ig_api_key')
        ig_acc_type = config.get('ig_acc_type', 'DEMO')  # Default to DEMO if not specified
        
        if not ig_username or not ig_password or not ig_api_key:
            print(f"Error: Bot {bot.id} missing IG Markets credentials in config")
            print(f"[IG] Username: {bool(ig_username)}, Password: {bool(ig_password)}, API Key: {bool(ig_api_key)}")
            return
        
        # Create IG Markets service instance with bot-specific credentials
        ig_service = IGMarketsService(
            username=ig_username,
            password=ig_password,
            api_key=ig_api_key,
            acc_type=ig_acc_type
        )
        
        if not ig_service.is_configured():
            print(f"Error: Cannot start bot {bot.id} - IG Markets not configured properly")
            print(f"[IG] Username: {ig_username}, API Key provided: {bool(ig_api_key)}")
            return
        
        self.active_bots[bot.id] = {
            'bot': bot,
            'ig_service': ig_service,
            'earnings_service': earnings_service,
            'task': None
        }
        
        # Start monitoring earnings
        task = asyncio.create_task(self._monitor_earnings_and_trade(bot, earnings_service, ig_service))
        self.active_bots[bot.id]['task'] = task
        
        # Start portfolio monitor (runs every minute)
        monitor_task = asyncio.create_task(self._monitor_portfolio(bot, ig_service))
        self.active_bots[bot.id]['monitor_task'] = monitor_task

    async def _monitor_portfolio(self, bot: Bot, ig_service: Any):
        """Monitor portfolio and update profitto.json every minute"""
        import json
        from datetime import datetime
        from models.user import get_db
        from models.bot import Bot
        
        print(f"[Bot {bot.id}] Starting portfolio monitor...")
        
        while True:
            try:
                # Check if bot is still active
                db_gen = get_db()
                db = next(db_gen)
                try:
                    current_bot = db.query(Bot).filter(Bot.id == bot.id).first()
                    if not current_bot or not current_bot.is_active:
                        break
                finally:
                    pass
                
                # Get current time
                now = datetime.now()
                current_time_str = now.strftime("%Y-%m-%d %H:%M:%S")
                
                # Get account info
                try:
                    account = await ig_service.get_account()
                    
                    # Calculate profit/loss
                    # profit_loss is the absolute value from IG
                    profit_loss_value = float(account.get('profit_loss', 0))
                    balance = float(account.get('balance', 0))
                    deposit = float(account.get('deposit', 0))
                    
                    # Calculate percentage based on deposit (initial capital)
                    # If deposit is 0 (shouldn't happen in active account), use balance - profit_loss
                    initial_capital = deposit if deposit > 0 else (balance - profit_loss_value)
                    
                    if initial_capital > 0:
                        profit_loss_percent = (profit_loss_value / initial_capital) * 100
                    else:
                        profit_loss_percent = 0.0
                    
                    # Create data structure
                    data = {
                        "timestamp": current_time_str,
                        "bot_id": bot.id,
                        "bot_name": bot.name,
                        "profit_loss_value": profit_loss_value,
                        "profit_loss_percent": round(profit_loss_percent, 2),
                        "total_balance": balance,
                        "available_cash": float(account.get('available', 0)),
                        "currency": account.get('currency', 'USD')
                    }
                    
                    # Write to profitto.json
                    file_path = os.path.join("backend", "profitto.json")
                    
                    # Read existing data to append or update? 
                    # User said "creare un file in json... aggiornato anche da ollama"
                    # We'll overwrite with the latest status for now, or append to a history list?
                    # "dive quanto è il profito... aggiornato" implies current state.
                    # Let's write the current state.
                    
                    with open(file_path, 'w') as f:
                        json.dump(data, f, indent=2)
                    
                    print(f"[Bot {bot.id}] Updated profitto.json: {profit_loss_value} ({profit_loss_percent:.2f}%)")
                    
                except Exception as e:
                    print(f"[Bot {bot.id}] Error fetching account info for monitor: {e}")
                
                # Wait 60 seconds
                await asyncio.sleep(60)
                
            except Exception as e:
                print(f"[Bot {bot.id}] Error in portfolio monitor: {e}")
                await asyncio.sleep(60)
    
    async def _monitor_earnings_and_trade(self, bot: Bot, earnings_service: Any, ig_service: Any):
        """Monitor earnings and execute trades for Earnings Report Genius bot with Gemini AI safety analysis"""
        from datetime import datetime, timedelta
        from models.user import get_db
        from models.bot import Bot
        from services.gemini_service import GeminiService
        
        # Get Gemini API key from bot config (required for earnings bot)
        config = bot.get_config()
        gemini_api_key = config.get('gemini_api_key')
        
        if not gemini_api_key:
            print(f"[Bot {bot.id}] Error: Gemini API key is required but not configured in bot settings")
            return
        
        gemini_service = GeminiService(api_key=gemini_api_key)
        
        # Track positions to close the next day
        pending_positions = {}  # {symbol: {'entry_date': date, 'order_id': str}}
        
        try:
            while True:
                # Check if bot is still active by refreshing from DB
                db_gen = get_db()
                db = next(db_gen)
                try:
                    current_bot = db.query(Bot).filter(Bot.id == bot.id).first()
                    if not current_bot or not current_bot.is_active:
                        break
                finally:
                    pass
                
                from services.earnings_service import get_next_business_days
                
                now = datetime.now().date()
                today, tomorrow = get_next_business_days(now)
                
                # Log if we skipped weekend
                if now != today:
                    print(f"[Bot {bot.id}] Skipped weekend: {now} -> {today} (next business day)")
                
                # Step 1: Close positions from previous earnings (day after entry)
                await self._close_earnings_positions(bot, ig_service, pending_positions, today)
                
                # Step 2: Get earnings for today and tomorrow (with cache 12h, skips weekends)
                print(f"[Bot {bot.id}] Checking earnings for {today} and {tomorrow}...")
                earnings = await earnings_service.get_earnings_today_tomorrow()
                
                # Filter earnings for today and tomorrow (business days)
                today_earnings = [e for e in earnings if e.get('date') == today.isoformat()]
                tomorrow_earnings = [e for e in earnings if e.get('date') == tomorrow.isoformat()]
                
                # Step 3: Analyze each earning with Gemini and allocate capital
                all_earnings = today_earnings + tomorrow_earnings
                
                if all_earnings:
                    # Get account info
                    try:
                        account = await ig_service.get_account()
                        available_cash = float(account.get('available', account.get('balance', 0)))
                        buying_power = float(account.get('available', available_cash))
                        
                        print(f"[Bot {bot.id}] Available cash: ${available_cash:,.2f}, Buying power: ${buying_power:,.2f}")
                        
                        if available_cash < 100:
                            print(f"[Bot {bot.id}] Insufficient cash to trade (need at least $100)")
                            await asyncio.sleep(3600)  # Wait 1 hour
                            continue
                        
                        # Analyze each earning and get safety scores
                        analyzed_earnings = []
                        
                        for earning in all_earnings:
                            symbol = earning.get('symbol', earning.get('ticker'))
                            company = earning.get('company', earning.get('companymearningsshortname', symbol))
                            earning_date = earning.get('date')
                            
                            if not symbol:
                                continue
                            
                            try:
                                # Get EPS history and reliability
                                eps_result = await earnings_service.get_ticker_eps_history(symbol, years=2)
                                eps_history = eps_result.get('quarters', [])
                                reliability = eps_result.get('reliability', {})
                                
                                # Analyze with Gemini
                                gemini_analysis = await gemini_service.analyze_earnings_safety(
                                    symbol=symbol,
                                    company=company,
                                    earnings_date=earning_date,
                                    eps_history=eps_history,
                                    reliability=reliability,
                                    available_cash=available_cash
                                )
                                
                                analyzed_earnings.append({
                                    'earning': earning,
                                    'symbol': symbol,
                                    'company': company,
                                    'earning_date': earning_date,
                                    'safety_score': gemini_analysis.get('safety_score', 0),
                                    'allocation_percentage': gemini_analysis.get('allocation_percentage', 0),
                                    'recommendation': gemini_analysis.get('recommendation', 'avoid'),
                                    'reasoning': gemini_analysis.get('reasoning', ''),
                                    'reliability': reliability
                                })
                                
                                print(f"[Bot {bot.id}] {symbol}: Safety={gemini_analysis.get('safety_score', 0)}, "
                                      f"Allocation={gemini_analysis.get('allocation_percentage', 0)*100:.1f}%, "
                                      f"Recommendation={gemini_analysis.get('recommendation', 'avoid')}")
                                
                            except Exception as e:
                                print(f"[Bot {bot.id}] Error analyzing {symbol}: {e}")
                                import traceback
                                traceback.print_exc()
                                continue
                        
                        # Step 4: Filter and sort by safety score
                        buy_recommendations = [
                            ae for ae in analyzed_earnings 
                            if ae['recommendation'] == 'buy' and ae['safety_score'] >= 50
                        ]
                        buy_recommendations.sort(key=lambda x: x['safety_score'], reverse=True)
                        
                        # Step 5: Execute trades based on allocation
                        positions = await ig_service.get_positions()
                        existing_epics = {p['epic'] for p in positions}
                        
                        for analyzed in buy_recommendations:
                            symbol = analyzed['symbol']
                            allocation = analyzed['allocation_percentage']
                            safety_score = analyzed['safety_score']
                            
                            # Get IG epic for symbol (IG uses epics, not stock symbols)
                            # First try direct mapping
                            epic = ig_service.get_epic_for_symbol(symbol)
                            
                            # Try to search for the epic if not found
                            if not epic:
                                try:
                                    print(f"[Bot {bot.id}] Searching IG Markets for {symbol}...")
                                    markets = await ig_service.search_markets(symbol)
                                    if markets and len(markets) > 0:
                                        epic = markets[0].get('epic')
                                        print(f"[Bot {bot.id}] Found epic {epic} for {symbol}")
                                    else:
                                        print(f"[Bot {bot.id}] {symbol}: Could not find IG epic, skipping")
                                        continue
                                except Exception as search_err:
                                    print(f"[Bot {bot.id}] {symbol}: Error searching for epic: {search_err}")
                                    # Try using the default format anyway
                                    epic = ig_service.get_epic_for_symbol(symbol)
                                    if not epic:
                                        continue
                            
                            # Verify epic exists by getting market info
                            try:
                                market_info = await ig_service.get_market_info(epic)
                                if not market_info or not market_info.get('current_price'):
                                    print(f"[Bot {bot.id}] {symbol}: Epic {epic} not valid or not available, skipping")
                                    continue
                            except Exception as verify_err:
                                print(f"[Bot {bot.id}] {symbol}: Error verifying epic {epic}: {verify_err}")
                                continue
                            
                            # Skip if we already have a position
                            if epic in existing_epics:
                                print(f"[Bot {bot.id}] Already have position in {symbol} ({epic}), skipping")
                                continue
                            
                            # Calculate allocation amount
                            allocation_amount = min(available_cash * allocation, buying_power * 0.3)  # Max 30% per stock
                            
                            if allocation_amount < 100:  # Minimum $100 per trade
                                print(f"[Bot {bot.id}] {symbol}: Allocation too small (${allocation_amount:.2f}), skipping")
                                continue
                            
                            try:
                                # Get market info to understand pricing
                                market_info = await ig_service.get_market_info(epic)
                                if not market_info or not market_info.get('current_price'):
                                    print(f"[Bot {bot.id}] {symbol}: Could not get market info, skipping")
                                    continue
                                
                                current_price = market_info.get('current_price', market_info.get('bid', 0))
                                
                                # IG Markets uses CFD - size is in currency units (dollars)
                                # For CFD, size represents the exposure in the base currency
                                # Example: size=100 means $100 exposure
                                # Calculate size based on allocation amount
                                # For CFD, we can directly use the allocation amount as size
                                position_size = max(1, int(allocation_amount))  # Minimum size of 1 unit
                                
                                # Place buy order before earnings (BUY direction)
                                print(f"[Bot {bot.id}] 📈 Opening BUY CFD position in {symbol} ({epic}) "
                                      f"size={position_size} units (${allocation_amount:,.2f}) before earnings - Safety: {safety_score:.1f}")
                                
                                order = await ig_service.place_market_order(
                                    epic=epic,
                                    direction='BUY',
                                    size=position_size
                                )
                                
                                if order:
                                    deal_reference = order.get('deal_reference')
                                    deal_id = order.get('deal_id')
                                    earning_date_obj = datetime.fromisoformat(analyzed['earning_date']).date()
                                    
                                    # Track position to close after earnings
                                    pending_positions[symbol] = {
                                        'epic': epic,
                                        'entry_date': earning_date_obj,
                                        'deal_id': deal_id,
                                        'deal_reference': deal_reference,
                                        'size': position_size,
                                        'direction': 'BUY',
                                        'safety_score': safety_score,
                                        'reasoning': analyzed['reasoning']
                                    }
                                    
                                    print(f"[Bot {bot.id}] ✅ Position opened: {deal_reference} for {symbol} ({epic})")
                                    self._log_activity(bot.id, f"OPEN BUY {symbol} ({epic}) size={position_size} - Safety Score: {safety_score}")
                                
                            except Exception as e:
                                print(f"[Bot {bot.id}] Error placing order for {symbol}: {e}")
                                import traceback
                                traceback.print_exc()
                                continue
                    except Exception as account_err:
                        print(f"[Bot {bot.id}] Error getting account info: {account_err}")
                        await asyncio.sleep(3600)
                        continue
                else:
                    print(f"[Bot {bot.id}] No earnings found for today/tomorrow")
                
                # Wait 1 hour before checking again
                await asyncio.sleep(3600)
        
        except Exception as e:
            print(f"[Bot {bot.id}] Error in bot execution: {e}")
            import traceback
            traceback.print_exc()
            # Update bot status to error
            db_gen = get_db()
            db = next(db_gen)
            try:
                current_bot = db.query(Bot).filter(Bot.id == bot.id).first()
                if current_bot:
                    current_bot.status = 'error'
                    db.commit()
            except Exception as db_err:
                print(f"Error updating bot status: {db_err}")
            finally:
                pass
    
    async def _close_earnings_positions(self, bot: Bot, ig_service: Any, pending_positions: Dict, today: date):
        """Close positions that were opened before earnings (close the day after entry)"""
        from datetime import datetime
        
        positions_to_close = []
        
        for symbol, position_info in pending_positions.items():
            entry_date = position_info.get('entry_date')
            if entry_date and entry_date < today:  # Entry was before today
                positions_to_close.append((symbol, position_info))
        
        for symbol, position_info in positions_to_close:
            try:
                deal_id = position_info.get('deal_id')
                epic = position_info.get('epic')
                direction = position_info.get('direction', 'BUY')
                size = position_info.get('size')
                
                if deal_id and epic:
                    print(f"[Bot {bot.id}] 📉 Closing position in {symbol} ({epic}) "
                          f"(entered {position_info['entry_date']}, size: {size}) after earnings")
                    
                    # Close position - direction should be opposite (if BUY, close with SELL)
                    close_direction = 'SELL' if direction == 'BUY' else 'BUY'
                    
                    order = await ig_service.close_position(
                        deal_id=deal_id,
                        direction=close_direction,
                        size=size  # None means close entire position
                    )
                    
                    if order:
                        print(f"[Bot {bot.id}] ✅ Position closed: {order.get('deal_reference')} for {symbol} ({epic})")
                        self._log_activity(bot.id, f"CLOSE {direction} {symbol} ({epic}) size={size}")
                        del pending_positions[symbol]
                    
            except Exception as e:
                print(f"[Bot {bot.id}] Error closing position in {symbol}: {e}")
                import traceback
                traceback.print_exc()
                # Keep in pending_positions to retry later
                continue

# Singleton instance
bot_service = BotService()

