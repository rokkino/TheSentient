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
    - Looks for post-market earnings today and pre-market earnings tomorrow
    - If nothing found, expands search to 5 days ahead
    - Uses Gemini to determine BUY/SELL with confidence
    - Creates paired orders: entry before earnings + exit after earnings
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
        
        # Get dates for the next 5 days
        today = datetime.now().date()
        search_dates = [today + timedelta(days=i) for i in range(5)]
        print(f"[JOB] Looking for earnings from {search_dates[0]} to {search_dates[-1]}")
        
        # First try with cache
        earnings_calendar = await earnings_service.get_earnings_calendar(months=1, use_cache=True)
        print(f"[JOB] Got {len(earnings_calendar)} total earnings from calendar")
        
        # Collect earnings by priority:
        # 1. Post-market today (highest priority - happening soonest)
        # 2. Pre-market tomorrow
        # 3. Post-market tomorrow
        # 4. Continue for next 5 days...
        relevant_earnings = []
        
        for e in earnings_calendar:
            try:
                date_str = e.get('date', '')
                if 'T' in date_str:
                    date_str = date_str.split('T')[0]
                e_date = datetime.fromisoformat(date_str).date()
                time_str = e.get('time', 'TBD')
                
                if e_date in search_dates:
                    # Add priority score (lower = higher priority)
                    day_offset = (e_date - today).days
                    time_priority = 0 if 'After' in time_str else 1 if 'Before' in time_str else 2
                    priority = day_offset * 10 + time_priority
                    
                    e['_priority'] = priority
                    e['_date'] = e_date
                    e['_time_slot'] = time_str
                    relevant_earnings.append(e)
            except:
                continue
        
        # Sort by priority
        relevant_earnings.sort(key=lambda x: x.get('_priority', 999))
        print(f"[JOB] Found {len(relevant_earnings)} earnings in next 5 days")
        
        # If no earnings found in cache, try fetching fresh
        if not relevant_earnings:
            print(f"[JOB] No cached earnings, fetching fresh data...")
            earnings_calendar = await earnings_service.get_earnings_calendar(months=1, use_cache=False)
            print(f"[JOB] Got {len(earnings_calendar)} total earnings after fresh fetch")
            
            for e in earnings_calendar:
                try:
                    date_str = e.get('date', '')
                    if 'T' in date_str:
                        date_str = date_str.split('T')[0]
                    e_date = datetime.fromisoformat(date_str).date()
                    time_str = e.get('time', 'TBD')
                    
                    if e_date in search_dates:
                        day_offset = (e_date - today).days
                        time_priority = 0 if 'After' in time_str else 1 if 'Before' in time_str else 2
                        priority = day_offset * 10 + time_priority
                        
                        e['_priority'] = priority
                        e['_date'] = e_date
                        e['_time_slot'] = time_str
                        relevant_earnings.append(e)
                except:
                    continue
            
            relevant_earnings.sort(key=lambda x: x.get('_priority', 999))
            print(f"[JOB] After fresh fetch: {len(relevant_earnings)} relevant earnings")
                
        if not relevant_earnings:
            print(f"[JOB] No earnings found in the next 5 days for bot {bot.name}")
            placeholder = Decision(
                bot_id=bot.id,
                symbol="MONITORING",
                decision="WAIT",
                reasoning=f"Bot is active and monitoring. No earnings found between {search_dates[0]} and {search_dates[-1]}. Will analyze when earnings are available.",
                execution_time=datetime.now().replace(hour=21, minute=59, second=0),
                status='PENDING'
            )
            db.add(placeholder)
            db.commit()
            return
            
        print(f"[JOB] Analyzing top {min(15, len(relevant_earnings))} earnings events for bot {bot.name}")
        
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
        
        # Market data for top candidates
        market_data_map = {}
        top_earnings = relevant_earnings[:15]  # Analyze top 15
        symbols = [e.get('symbol') for e in top_earnings]
        for symbol in symbols:
            try:
                data = market_data_service.get_market_data(symbol)
                market_data_map[symbol] = data
            except:
                pass
        
        opportunities = await bot_gemini.analyze_market_opportunities(top_earnings, market_data_map, current_time=str(datetime.now()))
        
        # Sort opportunities by confidence and pick the best ones
        # Debug: log all opportunities
        for opp in opportunities:
            print(f"[JOB] Opportunity: {opp.get('symbol')} {opp.get('decision')} conf={opp.get('confidence_score')}")
        
        valid_opportunities = [
            opp for opp in opportunities 
            if opp.get('decision') in ['BUY', 'SELL'] and opp.get('confidence_score', 0) >= 30  # Lowered threshold
        ]
        valid_opportunities.sort(key=lambda x: x.get('confidence_score', 0), reverse=True)
        
        print(f"[JOB] Found {len(valid_opportunities)} high-confidence opportunities")
        
        # Take top 5 most confident opportunities
        for opp in valid_opportunities[:5]:
            symbol = opp.get('symbol')
            decision_type = opp.get('decision')
            confidence_score = float(opp.get('confidence_score', 0) if opp.get('confidence_score') is not None else 0)
            
            # Find the corresponding earning to get the date
            earning_info = next((e for e in top_earnings if e.get('symbol') == symbol), None)
            earnings_date = earning_info.get('_date', today) if earning_info else today
            time_slot = earning_info.get('_time_slot', 'TBD') if earning_info else 'TBD'
            
            # Check if decision already exists for this symbol
            existing = db.query(Decision).filter(
                Decision.bot_id == bot.id,
                Decision.symbol == symbol,
                Decision.status.in_(['PENDING', 'EXECUTED']),
            ).first()
            
            if existing:
                print(f"[JOB] Skipping {symbol} - already have a pending/executed decision")
                continue
            
            # Calculate execution times based on earnings timing
            if 'After' in time_slot:
                # After market close earnings - execute at 21:59 on earnings day
                entry_time = datetime.combine(earnings_date, datetime.min.time()).replace(hour=21, minute=59)
                # Exit next morning at market open (9:30 AM next day)
                exit_time = datetime.combine(earnings_date + timedelta(days=1), datetime.min.time()).replace(hour=9, minute=35)
            else:  # Before market open
                # Before market earnings - execute previous day at 21:59
                entry_time = datetime.combine(earnings_date - timedelta(days=1), datetime.min.time()).replace(hour=21, minute=59)
                # Exit same day at 9:35 AM
                exit_time = datetime.combine(earnings_date, datetime.min.time()).replace(hour=9, minute=35)
            
            # If entry time is in the past, skip
            if entry_time < datetime.now():
                print(f"[JOB] Skipping {symbol} - entry time {entry_time} is in the past")
                continue
            
            reasoning_text = opp.get('reasoning', '')
            reasoning_text = f"[Confidence: {confidence_score:.0f}%] [Earnings: {earnings_date} {time_slot}] {reasoning_text}"
            
            # Create ENTRY decision
            entry_decision = Decision(
                bot_id=bot.id,
                symbol=symbol,
                decision=decision_type,  # BUY or SELL
                reasoning=f"ENTRY: {reasoning_text}",
                execution_time=entry_time,
                status='PENDING'
            )
            db.add(entry_decision)
            print(f"[JOB] Created ENTRY: {decision_type} {symbol} @ {entry_time}")
            
            # Create EXIT decision (opposite action)
            exit_decision_type = 'SELL' if decision_type == 'BUY' else 'BUY'
            exit_decision = Decision(
                bot_id=bot.id,
                symbol=symbol,
                decision=exit_decision_type,
                reasoning=f"EXIT (close position): Close {decision_type} position after earnings announcement",
                execution_time=exit_time,
                status='PENDING'
            )
            db.add(exit_decision)
            print(f"[JOB] Created EXIT: {exit_decision_type} {symbol} @ {exit_time}")
        
        db.commit()
        print(f"[JOB] Successfully processed earnings for bot {bot.name}")

    except Exception as e:
        print(f"[JOB] Error processing bot {bot_id}: {e}")
        import traceback
        traceback.print_exc()
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
                    original_symbol = decision.symbol
                    action = decision.decision # BUY/SELL
                    
                    if action in ["WAIT", "HOLD", "NO_GO", "MONITORING"]:
                        decision.status = "SKIPPED"
                        continue
                    
                    # Normalize symbol for Alpaca
                    from services.symbol_mapper import symbol_mapper
                    symbol = symbol_mapper.normalize_symbol(original_symbol)
                    
                    if symbol != original_symbol:
                        print(f"[JOB] Symbol normalized: {original_symbol} → {symbol}")
                    
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

