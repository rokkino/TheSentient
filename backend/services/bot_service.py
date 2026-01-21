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
        from services.alpaca_service import AlpacaService
        
        config = bot.get_config()
        earnings_service = EarningsService()
        
        broker = config.get('broker', 'IG')
        trading_service = None
        
        if broker == 'Alpaca':
            # Initialize Alpaca Service
            api_key = config.get('alpaca_api_key')
            api_secret = config.get('alpaca_api_secret')
            is_paper = config.get('alpaca_paper', True)
            
            if not api_key or not api_secret:
                print(f"Error: Bot {bot.id} missing Alpaca credentials")
                return
                
            trading_service = AlpacaService(api_key=api_key, api_secret=api_secret, paper=is_paper)
            
            if not trading_service.is_configured():
                print(f"Error: Cannot start bot {bot.id} - Alpaca not configured properly")
                return
                
        else:
            # Initialize IG Markets Service
            ig_username = config.get('ig_username')
            ig_password = config.get('ig_password')
            ig_api_key = config.get('ig_api_key')
            ig_acc_type = config.get('ig_acc_type', 'DEMO')
            
            if not ig_username or not ig_password or not ig_api_key:
                print(f"Error: Bot {bot.id} missing IG Markets credentials in config")
                return
            
            trading_service = IGMarketsService(
                username=ig_username,
                password=ig_password,
                api_key=ig_api_key,
                acc_type=ig_acc_type
            )
            
            if not trading_service.is_configured():
                print(f"Error: Cannot start bot {bot.id} - IG Markets not configured properly")
                return
        
        self.active_bots[bot.id] = {
            'bot': bot,
            'trading_service': trading_service,
            'earnings_service': earnings_service,
            'task': None,
            'broker': broker
        }
        
        # Start monitoring earnings
        task = asyncio.create_task(self._monitor_earnings_and_trade(bot, earnings_service, trading_service, broker))
        self.active_bots[bot.id]['task'] = task
        
        # Start portfolio monitor (runs every minute)
        monitor_task = asyncio.create_task(self._monitor_portfolio(bot, trading_service))
        self.active_bots[bot.id]['monitor_task'] = monitor_task
        
        # ... (rest of the logic)
        
        # Actually, let's look at the plan. "Initialize AlpacaService".
        # I'll modify AlpacaService to accept keys.
        
        # Let's just do the IG part for now and then I'll fix AlpacaService.
        # Or better, I'll do a multi-file edit if possible? No, `replace_file_content` is single file.
        # I will cancel this tool call and do AlpacaService first.


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
    
    async def _monitor_earnings_and_trade(self, bot: Bot, earnings_service: Any, trading_service: Any, broker: str = 'IG'):
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
                await self._close_earnings_positions(bot, trading_service, pending_positions, today, broker)
                
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
                        account = await trading_service.get_account()
                        
                        if broker == 'Alpaca':
                            available_cash = float(account.get('cash', 0))
                            buying_power = float(account.get('buying_power', available_cash))
                        else: # IG
                            available_cash = float(account.get('available', account.get('balance', 0)))
                            buying_power = float(account.get('available', available_cash))
                        
                        print(f"[Bot {bot.id}] Available cash: ${available_cash:,.2f}, Buying power: ${buying_power:,.2f}")
                        
                        if available_cash < 100:
                            print(f"[Bot {bot.id}] Insufficient cash to trade (need at least $100)")
                            await asyncio.sleep(60)  # Wait 1 minute
                            continue
                        
                        # Analyze each earning
                        for earning in all_earnings:
                            symbol = earning.get('symbol', earning.get('ticker'))
                            company = earning.get('company', earning.get('companymearningsshortname', symbol))
                            earning_date = earning.get('date')
                            
                            if not symbol:
                                continue
                            
                            # Skip if we already have a position
                            positions = await trading_service.get_positions()
                            has_position = False
                            if broker == 'IG':
                                epic = trading_service.get_epic_for_symbol(symbol)
                                if epic:
                                    existing_epics = {p['epic'] for p in positions}
                                    if epic in existing_epics:
                                        has_position = True
                            else:
                                existing_symbols = {p['symbol'] for p in positions}
                                if symbol in existing_symbols:
                                    has_position = True
                            
                            if has_position:
                                print(f"[Bot {bot.id}] Already have position in {symbol}, skipping analysis")
                                continue

                            try:
                                # Get comprehensive market data using market_data_service
                                from services.market_data_service import market_data_service
                                
                                market_data = market_data_service.get_stock_data(symbol)
                                current_price = market_data.get('current_price', 0.0)
                                short_interest = market_data.get('short_interest', 'N/A')
                                iv_rank = market_data.get('iv_rank', 'N/A')
                                pe_ratio = market_data.get('pe_ratio')
                                two_week_change = market_data.get('two_week_change_pct', 0)
                                run_up_warning = market_data.get('run_up_warning', False)
                                
                                # Get analyst revisions
                                analyst_data = market_data_service.get_analyst_revisions(symbol)
                                analyst_trend = analyst_data.get('trend', 'N/A')
                                
                                current_time_str = datetime.now().strftime("%H:%M")
                                
                                # Log market data
                                print(f"[Bot {bot.id}] {symbol} Market Data:")
                                print(f"  Price: ${current_price}, P/E: {pe_ratio}, Short: {short_interest}, IV: {iv_rank}")
                                print(f"  2-Week Change: {two_week_change}%, Analyst Trend: {analyst_trend}")
                                if run_up_warning:
                                    print(f"  ⚠️  RUN-UP WARNING: Stock up {two_week_change}% in 2 weeks!")
                                
                                # Get EPS history and reliability
                                eps_result = await earnings_service.get_ticker_eps_history(symbol, years=2)
                                eps_history = eps_result.get('quarters', [])
                                reliability = eps_result.get('reliability', {})
                                
                                # Analyze with Gemini (acting as "Earnings Genius")
                                gemini_analysis = await gemini_service.analyze_earnings_safety(
                                    symbol=symbol,
                                    company=company,
                                    earnings_date=earning_date,
                                    eps_history=eps_history,
                                    reliability=reliability,
                                    available_cash=available_cash,
                                    current_price=current_price,
                                    current_time=current_time_str,
                                    short_interest=short_interest,
                                    iv_rank=iv_rank
                                )
                                
                                decision = gemini_analysis.get('decision', 'NO_GO')
                                confidence = gemini_analysis.get('confidence_score', 0)
                                reasoning = gemini_analysis.get('reasoning_summary', '')
                                entry_zone = gemini_analysis.get('entry_zone', {})
                                ideal_price = entry_zone.get('ideal_price')
                                max_entry_price = entry_zone.get('max_entry_price')
                                
                                print(f"[Bot {bot.id}] {symbol}: Decision={decision}, Confidence={confidence}, Price=${current_price}")
                                print(f"[Bot {bot.id}] Reasoning: {reasoning}")
                                
                                if decision == 'BUY':
                                    # Check price conditions
                                    if current_price > 0 and max_entry_price and current_price > max_entry_price:
                                        print(f"[Bot {bot.id}] {symbol}: Price ${current_price} is above max entry ${max_entry_price}. WAITING.")
                                        continue
                                        
                                    # Execute BUY
                                    allocation_percentage = 0.1 # Default 10% for now as per strategy or dynamic?
                                    # Strategy says "allocation_percentage" might be in JSON but user prompt didn't strictly require it in JSON output
                                    # User prompt had "entry_zone". 
                                    # Let's use a safe default or if Gemini provided it in "allocation_percentage" (legacy field I kept)
                                    allocation_percentage = gemini_analysis.get('allocation_percentage', 0.1)
                                    
                                    allocation_amount = min(available_cash * allocation_percentage, buying_power * 0.3)
                                    
                                    if allocation_amount < 100:
                                        print(f"[Bot {bot.id}] Allocation too small, skipping")
                                        continue
                                        
                                    print(f"[Bot {bot.id}] 🚀 EXECUTING BUY for {symbol} based on Earnings Genius decision!")
                                    
                                    # Place order logic (reused from before)
                                    if broker == 'IG':
                                        epic = trading_service.get_epic_for_symbol(symbol)
                                        if epic:
                                            position_size = max(1, int(allocation_amount)) # CFD units
                                            order = await trading_service.place_market_order(
                                                epic=epic,
                                                direction='BUY',
                                                size=position_size
                                            )
                                            if order:
                                                deal_ref = order.get('deal_reference')
                                                print(f"[Bot {bot.id}] Order placed: {deal_ref}")
                                                self._log_activity(bot.id, f"BUY {symbol} ({epic}) - {reasoning}")
                                                
                                                # Track for exit
                                                pending_positions[symbol] = {
                                                    'epic': epic,
                                                    'entry_date': now, # Today
                                                    'deal_reference': deal_ref,
                                                    'size': position_size,
                                                    'direction': 'BUY',
                                                    'reasoning': reasoning
                                                }
                                    
                                elif decision == 'WAIT':
                                    print(f"[Bot {bot.id}] {symbol}: Waiting for better entry or conditions.")
                                    
                                elif decision == 'NO_GO':
                                    print(f"[Bot {bot.id}] {symbol}: NO_GO. Skipping.")
                                
                            except Exception as e:
                                print(f"[Bot {bot.id}] Error analyzing {symbol}: {e}")
                                import traceback
                                traceback.print_exc()
                                continue
                        
                    except Exception as account_err:
                        print(f"[Bot {bot.id}] Error getting account info: {account_err}")
                        await asyncio.sleep(60)
                        continue
                else:
                    print(f"[Bot {bot.id}] No earnings found for today/tomorrow")
                
                # Wait 1 minute (Llama tactical monitoring frequency)
                await asyncio.sleep(60)
        
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
    
    async def _close_earnings_positions(self, bot: Bot, trading_service: Any, pending_positions: Dict, today: date, broker: str = 'IG'):
        """Close positions that were opened before earnings (close the day after entry)"""
        from datetime import datetime
        
        positions_to_close = []
        
        for symbol, position_info in pending_positions.items():
            entry_date = position_info.get('entry_date')
            if entry_date and entry_date < today:  # Entry was before today
                positions_to_close.append((symbol, position_info))
        
        for symbol, position_info in positions_to_close:
            try:
                if broker == 'IG':
                    deal_id = position_info.get('deal_id')
                    epic = position_info.get('epic')
                    direction = position_info.get('direction', 'BUY')
                    size = position_info.get('size')
                    
                    if deal_id and epic:
                        print(f"[Bot {bot.id}] 📉 Closing position in {symbol} ({epic}) "
                              f"(entered {position_info['entry_date']}, size: {size}) after earnings")
                        
                        # Close position - direction should be opposite (if BUY, close with SELL)
                        close_direction = 'SELL' if direction == 'BUY' else 'BUY'
                        
                        order = await trading_service.close_position(
                            deal_id=deal_id,
                            direction=close_direction,
                            size=size  # None means close entire position
                        )
                        
                        if order:
                            print(f"[Bot {bot.id}] ✅ Position closed: {order.get('deal_reference')} for {symbol} ({epic})")
                            self._log_activity(bot.id, f"CLOSE {direction} {symbol} ({epic}) size={size}")
                            del pending_positions[symbol]
                
                elif broker == 'Alpaca':
                    print(f"[Bot {bot.id}] 📉 Closing position in {symbol} after earnings (Alpaca)")
                    await trading_service.close_position(symbol)
                    del pending_positions[symbol]
                    
            except Exception as e:
                print(f"[Bot {bot.id}] Error closing position in {symbol}: {e}")
                import traceback
                traceback.print_exc()
                # Keep in pending_positions to retry later
                continue

# Singleton instance
bot_service = BotService()

