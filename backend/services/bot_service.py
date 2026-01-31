"""
Bot Service - Handles bot management, configuration, and execution
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from models.bot import Bot
from models.user import User
from datetime import datetime, date, timedelta, timezone
import asyncio
import asyncio
import os
import json
from models.account import Account
from models.user import SessionLocal

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
        bot.updated_at = datetime.now(timezone.utc)
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
        bot.activated_at = datetime.now(timezone.utc)
        bot.updated_at = datetime.now(timezone.utc)
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
        bot.updated_at = datetime.now(timezone.utc)
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
    
    def _get_configured_service(self, db: Session, bot: Bot) -> Optional[Any]:
        """Get trading service instance configured for this bot"""
        config = bot.get_config()
        broker = config.get('broker', 'IG')
        
        # Resolve credentials
        credentials = {}
        account_id = config.get('account_id')
        
        if account_id:
            account = db.query(Account).filter(Account.id == account_id).first()
            if account:
                try:
                    credentials = json.loads(account.credentials)
                    # Add platform specific mapping if needed
                    if account.platform == 'IG':
                         credentials['account_type'] = credentials.get('account_type', 'DEMO')
                    elif account.platform == 'Alpaca':
                         credentials['paper'] = credentials.get('paper_trading', True)
                except:
                    pass
        else:
             # Use legacy config fields
             if broker == 'IG':
                 credentials = {
                     'username': config.get('ig_username'),
                     'password': config.get('ig_password'),
                     'api_key': config.get('ig_api_key'),
                     'account_type': config.get('ig_acc_type', 'DEMO')
                 }
             elif broker == 'Alpaca':
                 credentials = {
                     'api_key': config.get('alpaca_api_key'),
                     'secret_key': config.get('alpaca_api_secret'),
                     'paper': config.get('alpaca_paper', True)
                 }

        # Instantiate Service
        if broker == 'IG':
            from services.ig_service import IGMarketsService
            if credentials.get('username') or credentials.get('api_key'):
                return IGMarketsService(
                    username=credentials.get('username'),
                    password=credentials.get('password'),
                    api_key=credentials.get('api_key'),
                    acc_type=credentials.get('account_type', 'DEMO')
                )
        elif broker == 'Alpaca':
            from services.alpaca_service import AlpacaService
            if credentials.get('api_key'):
                return AlpacaService(
                    api_key=credentials.get('api_key'),
                    api_secret=credentials.get('secret_key'),
                    paper=credentials.get('paper', True)
                )
        
        return None
    
    async def _start_bot(self, bot: Bot):
        """Start bot execution based on bot type"""
        try:
            print(f"[BotService] Starting bot {bot.id} ({bot.name})...")
            
            # Add to active bots tracking
            self.active_bots[bot.id] = True
            
            # Specific logic for Earnings Report Genius
            if "Earnings" in bot.name or "Earnings" in (bot.description or ""):
                print(f"[BotService] Triggering immediate earnings analysis for bot {bot.id}...")
                # Import here to avoid circular dependencies
                from services.scheduler_jobs import process_bot_earnings
                await process_bot_earnings(bot.id)
            
            # Resolve trading service (IG or Alpaca)
            service = None
            db = SessionLocal()
            try:
                # Reload bot from this session to ensure attached state if needed, or just use ID
                current_bot = db.query(Bot).filter(Bot.id == bot.id).first()
                if current_bot:
                   service = self._get_configured_service(db, current_bot)
            finally:
                db.close()
            
            # Start portfolio monitoring
            if service:
                 print(f"[BotService] Starting portfolio monitor for bot {bot.id}...")
                 asyncio.create_task(self._monitor_portfolio(bot, service))
            else:
                 print(f"[BotService] No trading service configured for bot {bot.id}, skipping monitor.")
            
        except Exception as e:
            print(f"[BotService] Error starting bot {bot.id}: {e}")

    



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
    


# Singleton instance
bot_service = BotService()

