import asyncio
from datetime import datetime, date
from sqlalchemy.orm import Session

from services.gemini_service import GeminiService
from services.market_data import MarketDataService
from models.user import SessionLocal, User
from models.bot import Decision, Bot
from services.scheduler_service import scheduler_service
from services.alpaca_service import alpaca_service
from datetime import timedelta

# Initialize services

gemini_service = GeminiService()
market_data_service = MarketDataService()

async def process_bot_earnings(bot_id: int):
    """
    Analyze earnings for a specific bot immediately.
    """
    print(f"[JOB] Processing earnings for bot {bot_id}...")
    db = SessionLocal()
    try:
        bot = db.query(Bot).filter(Bot.id == bot_id).first()
        if not bot or not bot.is_active:
             print(f"[JOB] Bot {bot_id} not found or inactive")
             return

        user = db.query(User).filter(User.id == bot.user_id).first()
        if not user:
             return

        # Get earnings data
        from services.earnings_service import earnings_service
        # For immediate trigger, we force refresh or use cache? Use cache for speed.
        earnings_calendar = await earnings_service.get_earnings_calendar(months=1, use_cache=True)
        
        # Filter for today/tomorrow
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)
        
        relevant_earnings = []
        for e in earnings_calendar:
            try:
                date_str = e.get('date', '')
                if 'T' in date_str:
                    date_str = date_str.split('T')[0]
                e_date = datetime.fromisoformat(date_str).date()
                if e_date == today or e_date == tomorrow:
                    relevant_earnings.append(e)
            except:
                continue
                
        if not relevant_earnings:
            print(f"[JOB] No relevant earnings found for bot {bot.name}")
            return
            
        print(f"[JOB] Analyzing {len(relevant_earnings)} earnings events for bot {bot.name}")
        
        # Instantiate GeminiService with USER'S API KEY
        user_api_key = user.gemini_api_key
        user_model = getattr(user, 'gemini_model', None)
        
        if not user_api_key:
            print(f"[JOB] Skipping bot {bot.name}: No Gemini API key")
            return
            
        bot_gemini = GeminiService(api_key=user_api_key, model_name=user_model)
        
        if not bot_gemini.available:
            print(f"[JOB] Skipping bot {bot.name}: Gemini service unavailable")
            return
        
        # Market data
        market_data_map = {}
        symbols = [e.get('symbol') for e in relevant_earnings]
        for symbol in symbols[:10]:
                try:
                    data = market_data_service.get_market_data(symbol)
                    market_data_map[symbol] = data
                except:
                    pass
        
        opportunities = await bot_gemini.analyze_market_opportunities(relevant_earnings[:10], market_data_map, current_time=str(datetime.now()))
        
        # Save Decisions
        for opp in opportunities:
            symbol = opp.get('symbol')
            decision_type = opp.get('decision')
            
            if decision_type in ['BUY', 'SELL']:
                    # Check if decision already exists for this symbol today
                    existing = db.query(Decision).filter(
                        Decision.bot_id == bot.id,
                        Decision.symbol == symbol,
                        Decision.status.in_(['PENDING', 'EXECUTED', 'FAILED']),
                        Decision.created_at >= datetime.now().replace(hour=0, minute=0, second=0)
                    ).first()
                    
                    if existing:
                        continue
                        
                    # Create new decision
                    # Note: Decision model doesn't have confidence field, include it in reasoning
                    confidence_score = float(opp.get('confidence_score', 0) if opp.get('confidence_score') is not None else 0)
                    reasoning_text = opp.get('reasoning', '')
                    if confidence_score > 0:
                        reasoning_text = f"[Confidence: {confidence_score:.0f}%] {reasoning_text}"
                    
                    new_decision = Decision(
                        bot_id=bot.id,
                        symbol=symbol,
                        decision=decision_type,
                        reasoning=reasoning_text,
                        execution_time=datetime.now() if opp.get('execution_time') == 'IMMEDIATE' else datetime.now().replace(hour=21, minute=59, second=0),
                        status='PENDING'
                    )
                    db.add(new_decision)
                    print(f"[JOB] Created decision for {bot.name}: {decision_type} {symbol}")
        
        db.commit()

    except Exception as e:
        print(f"[JOB] Error processing bot {bot_id}: {e}")
    finally:
        db.close()

async def analyze_earnings_job():
    """
    Job to analyze earnings and generate trading decisions.
    Runs every 30 minutes.
    """
    job_name = "analyze_earnings"
    print(f"[JOB] Starting {job_name}...")
    
    db = SessionLocal()
    try:
        # Get active bots
        active_bots = db.query(Bot).filter(Bot.is_active == True).all()
        if not active_bots:
            print("[JOB] No active bots found")
            return

        print(f"[JOB] Found {len(active_bots)} active bots")
        
        # Process each bot individually (could be parallelized)
        for bot in active_bots:
            await process_bot_earnings(bot.id)
                
    except Exception as e:
        print(f"[JOB] Error in analyze_earnings_job: {e}")
    finally:
        db.close()



async def execute_orders_job():
    """
    Job to execute pending orders.
    Runs every 1 minute.
    """
    job_name = "execute_orders"
    print(f"[JOB] Starting {job_name}...")
    
    db = SessionLocal()
    try:
        now = datetime.now()
        
        # Find pending orders due for execution
        pending_decisions = db.query(Decision).filter(
            Decision.status == "PENDING",
            Decision.execution_time <= now
        ).all()
        
        if not pending_decisions:
            return

        print(f"[JOB] Found {len(pending_decisions)} orders to execute")
        
        # Group by bot_id to verify configuration once per bot
        from services.bot_service import bot_service
        from services.ig_service import IGMarketsService
        from services.alpaca_service import AlpacaService
        
        decisions_by_bot = {}
        for d in pending_decisions:
            if d.bot_id not in decisions_by_bot:
                decisions_by_bot[d.bot_id] = []
            decisions_by_bot[d.bot_id].append(d)
            
        for bot_id, decisions in decisions_by_bot.items():
            bot = db.query(Bot).filter(Bot.id == bot_id).first()
            if not bot:
                 continue
            
            # Get service for this bot
            service = bot_service._get_configured_service(db, bot)
            
            if not service:
                print(f"[JOB] No service configured for bot {bot.name} (ID: {bot.id})")
                for d in decisions:
                    d.status = "FAILED"
                    d.reasoning = (d.reasoning or "") + " | Trading service not configured"
                continue
                
            for decision in decisions:
                try:
                    symbol = decision.symbol
                    action = decision.decision # BUY/SELL
                    
                    if action in ["WAIT", "HOLD", "NO_GO"]:
                        decision.status = "SKIPPED"
                        continue
                    
                    print(f"[JOB] Executing {action} {symbol} for bot {bot.name}...")
                    qty = 1 # Default quantity
                    
                    order_result = None
                    
                    if isinstance(service, IGMarketsService):
                        # IG Execution
                        epic = service.get_epic_for_symbol(symbol)
                        if not epic:
                            raise Exception(f"Could not resolve epic for {symbol}")
                        
                        order_result = await service.place_market_order(
                            epic=epic,
                            direction=action.upper(),
                            size=qty
                        )
                    elif isinstance(service, AlpacaService):
                        # Alpaca Execution
                        order_result = await service.place_market_order(
                            symbol=symbol,
                            qty=qty,
                            side=action.lower()
                        )
                    else:
                        raise Exception("Unknown service type")

                    decision.status = "EXECUTED"
                    decision.executed_at = datetime.now()
                    # Extract ID from result if possible
                    order_id = order_result.get('deal_reference') or order_result.get('id') or 'N/A'
                    decision.reasoning = (decision.reasoning or "") + f" | Order ID: {order_id}"
                    
                    scheduler_service.log_execution(job_name, "SUCCESS", f"Executed {action} {symbol} (Bot {bot.name})")
                    
                except Exception as e:
                    print(f"[JOB] Error executing order for {decision.symbol}: {e}")
                    decision.status = "FAILED"
                    decision.reasoning = (decision.reasoning or "") + f" | Error: {str(e)}"
                    scheduler_service.log_execution(job_name, "ERROR", f"Failed {decision.symbol}: {e}")
        
        db.commit()
        
    except Exception as e:
        print(f"[JOB] Error in execute_orders_job: {e}")
        scheduler_service.log_execution(job_name, "ERROR", str(e))
    finally:
        db.close()

