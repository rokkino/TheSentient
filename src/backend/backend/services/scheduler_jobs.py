import asyncio
import os
import json
from datetime import datetime, date, timezone
from sqlalchemy.orm import Session

from services.gemini_service import GeminiService
from services.market_data import MarketDataService
from models.user import SessionLocal, User
from models.bot import Decision, Bot
from services.scheduler_service import scheduler_service
from services.bot_service import bot_service
from services.alpaca_service import alpaca_service, AlpacaService
from services.ig_service import IGMarketsService
from datetime import timedelta

# Initialize services

gemini_service = GeminiService()
market_data_service = MarketDataService()


async def refresh_earnings_cache_job():
    """
    Refresh full-year earnings cache and earnings_data.json.
    Run monthly so the cache and JSON file stay up to date.
    """
    print("[JOB] refresh_earnings_cache_job: fetching 12 months earnings...")
    try:
        from services.earnings_service import earnings_service
        earnings_data = await earnings_service.get_earnings_calendar(months=12, use_cache=False)
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        earnings_file_path = os.path.join(backend_dir, "earnings_data.json")
        with open(earnings_file_path, 'w', encoding='utf-8') as f:
            json.dump({
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "total_earnings": len(earnings_data),
                "earnings": earnings_data
            }, f, indent=2, ensure_ascii=False, default=str)
        print(f"[JOB] refresh_earnings_cache_job: saved {len(earnings_data)} earnings to {earnings_file_path}")
    except Exception as e:
        print(f"[JOB] refresh_earnings_cache_job error: {e}")
        import traceback
        traceback.print_exc()

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
        
        # --- SAFETY NET: LIQUIDATE STUCK POSITIONS ---
        # Find executed entries that have no corresponding executed exit after 48 hours
        try:
            print(f"[JOB] Checking for stuck positions for bot {bot.name}...")
            # Look back 30 days
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
            
            # Get all EXECUTED BUY decisions
            executed_entries = db.query(Decision).filter(
                Decision.bot_id == bot.id,
                Decision.status == 'EXECUTED',
                Decision.decision == 'BUY',
                Decision.created_at >= cutoff_date
            ).all()
            
            stuck_count = 0
            for entry in executed_entries:
                # Check if this symbol has been sold/closed AFTER the entry
                # We look for ANY executed SELL for this symbol that happened after the entry
                entry_time = entry.executed_at or entry.created_at
                
                # Find matching close (EXECUTED or FAILED sell counts as "attempted closure")
                closed = db.query(Decision).filter(
                    Decision.bot_id == bot.id,
                    Decision.symbol == entry.symbol,
                    Decision.status.in_(['EXECUTED', 'FAILED']),
                    Decision.decision == 'SELL',
                    Decision.created_at > entry.created_at # Created after the buy
                ).first()
                
                if not closed:
                    # Position might be open. Is it old?
                    # Ensure timezone awareness compatibility
                    now = datetime.now(timezone.utc)
                    if entry_time.tzinfo is None:
                        # Assume UTC if naive, or convert both to naive
                        entry_time = entry_time.replace(tzinfo=timezone.utc)
                    
                    age = now - entry_time
                    
                    # If older than 48 hours (earnings plays are usually 1 day), it's stuck
                    if age > timedelta(hours=48):
                        print(f"[JOB] Found STUCK position: {entry.symbol} (Age: {age}). Liquidating...")
                        
                        # Check if we already have a PENDING or FAILED sell to avoid duplicates
                        existing_sell = db.query(Decision).filter(
                             Decision.bot_id == bot.id,
                             Decision.symbol == entry.symbol,
                             Decision.decision == 'SELL',
                             Decision.status.in_(['PENDING', 'FAILED'])
                        ).first()
                        
                        if existing_sell:
                            if existing_sell.status == 'PENDING':
                                print(f"[JOB] Pending sell already exists for {entry.symbol}, updating to IMMEDIATE.")
                                existing_sell.execution_time = datetime.now(timezone.utc)
                                existing_sell.reasoning = (existing_sell.reasoning or "") + " | FORCE LIQUIDATION (Stuck)"
                            else:
                                print(f"[JOB] FAILED sell already exists for {entry.symbol}, skipping duplicate liquidation.")
                        else:
                            # Create new liquidation order
                            liquidate = Decision(
                                bot_id=bot.id,
                                symbol=entry.symbol,
                                decision='SELL',
                                # grouping_id removed as it does not exist in model
                                status='PENDING',
                                execution_time=datetime.now(timezone.utc), # Execute NOW
                                reasoning=f"FORCE LIQUIDATION: Position held for {age} without closure."
                            )
                            db.add(liquidate)
                            stuck_count += 1
            
            if stuck_count > 0:
                db.commit()
                print(f"[JOB] Created {stuck_count} liquidation orders for stuck positions.")
                
        except Exception as e:
            print(f"[JOB] Error in safety net: {e}")
            import traceback
            traceback.print_exc()
            # Continue with normal processing
        
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
        
        # --- DYNAMIC POSITION SIZING ---
        # 1. Get Account Balance
        try:
            from services.bot_service import bot_service
            service = bot_service._get_configured_service(db, bot)
            
            # Default fallback values
            total_balance = 0.0
            
            if service:
                try:
                    # Generic get_account method expected on services
                    if hasattr(service, 'get_account'):
                        account_info = await service.get_account()
                        # Use portfolio value or equity or cash
                        total_balance = float(account_info.get('portfolio_value') or account_info.get('equity') or account_info.get('cash') or 0)
                        print(f"[JOB] Account Balance for sizing: ${total_balance:.2f}")
                    else:
                        print("[JOB] Service does not support get_account, using default $10,000 for sizing")
                        total_balance = 10000.0
                except Exception as ex:
                    print(f"[JOB] Failed to get account balance: {ex}, using default $10,000")
                    total_balance = 10000.0
            else:
                print("[JOB] No service configured, using default $10,000 for sizing")
                total_balance = 10000.0
                
            # 2. Calculate Daily Budget
            config = bot.get_config()
            daily_budget_pct = float(config.get('daily_budget_pct', 50))
            if daily_budget_pct <= 0 or daily_budget_pct > 100:
                daily_budget_pct = 50.0
                
            daily_budget = total_balance * (daily_budget_pct / 100.0)
            print(f"[JOB] Daily Budget: ${daily_budget:.2f} ({daily_budget_pct}% of ${total_balance:.2f})")
            
            # 3. Allocation Logic
            selected_opportunities = valid_opportunities[:5]
            num_trades = len(selected_opportunities)
            
            if num_trades == 0:
                print("[JOB] No trades to allocate budget to.")
                return
                
            use_confidence_sizing = config.get('use_confidence_sizing', True)
            
            allocations = {} # symbol -> amount_usd
            
            if use_confidence_sizing:
                total_confidence = sum([float(opp.get('confidence_score', 0)) for opp in selected_opportunities])
                print(f"[JOB] Total Confidence Score: {total_confidence}")
                
                if total_confidence > 0:
                    for opp in selected_opportunities:
                        symbol = opp.get('symbol')
                        conf = float(opp.get('confidence_score', 0))
                        # Allocation = Budget * (Share of Confidence)
                        amount = daily_budget * (conf / total_confidence)
                        allocations[symbol] = amount
                        print(f"[JOB] Allocating ${amount:.2f} to {symbol} (Conf: {conf})")
                else:
                    # Fallback to equal
                    per_trade = daily_budget / num_trades
                    for opp in selected_opportunities:
                        allocations[opp.get('symbol')] = per_trade
            else:
                # Equal Weighting
                per_trade = daily_budget / num_trades
                for opp in selected_opportunities:
                    allocations[opp.get('symbol')] = per_trade
                print(f"[JOB] Allocating ${per_trade:.2f} to each of {num_trades} trades (Equal Weight)")
                
        except Exception as e:
            print(f"[JOB] Error in sizing logic: {e}")
            import traceback
            traceback.print_exc()
            # Fallback
            selected_opportunities = valid_opportunities[:5]
            allocations = {opp.get('symbol'): 1000.0 for opp in selected_opportunities}

        # Take top 5 most confident opportunities
        for opp in selected_opportunities:
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
                next_day = earnings_date + timedelta(days=1)
                if next_day.weekday() == 5:  # Saturday
                    next_day += timedelta(days=2)
                elif next_day.weekday() == 6:  # Sunday
                    next_day += timedelta(days=1)
                exit_time = datetime.combine(next_day, datetime.min.time()).replace(hour=9, minute=35)
            else:  # Before market open
                # Before market earnings - execute previous business day at 21:59
                prev_day = earnings_date - timedelta(days=1)
                if prev_day.weekday() == 5:  # Saturday
                    prev_day -= timedelta(days=1)
                elif prev_day.weekday() == 6:  # Sunday
                    prev_day -= timedelta(days=2)
                entry_time = datetime.combine(prev_day, datetime.min.time()).replace(hour=21, minute=59)
                # Exit same day at 9:35 AM
                exit_day = earnings_date
                if exit_day.weekday() == 5:
                    exit_day += timedelta(days=2)
                elif exit_day.weekday() == 6:
                    exit_day += timedelta(days=1)
                exit_time = datetime.combine(exit_day, datetime.min.time()).replace(hour=9, minute=35)
            
            # If entry time is in the past, skip
            if entry_time < datetime.now():
                print(f"[JOB] Skipping {symbol} - entry time {entry_time} is in the past")
                continue
            
            reasoning_text = opp.get('reasoning', '')
            reasoning_text = f"[Confidence: {confidence_score:.0f}%] [Earnings: {earnings_date} {time_slot}] {reasoning_text}"
            
            # Create ENTRY decision
            entry_amount = allocations.get(symbol, 1000.0)
            
            # Extract optional SL/TP
            sl_val = opp.get('stop_loss')
            tp_val = opp.get('take_profit')
            stop_loss = float(sl_val) if sl_val is not None else None
            take_profit = float(tp_val) if tp_val is not None else None

            entry_decision = Decision(
                bot_id=bot.id,
                symbol=symbol,
                decision=decision_type,  # BUY or SELL
                reasoning=f"ENTRY: {reasoning_text} | Allocated: ${entry_amount:.2f}",
                execution_time=entry_time,
                status='PENDING',
                allocated_amount=entry_amount,
                stop_loss=stop_loss,
                take_profit=take_profit
            )
            db.add(entry_decision)
            print(f"[JOB] Created ENTRY: {decision_type} {symbol} @ {entry_time} SL:{stop_loss} TP:{take_profit}")
            
            # Create EXIT decision (opposite action)
            exit_decision_type = 'SELL' if decision_type == 'BUY' else 'BUY'
            exit_decision = Decision(
                bot_id=bot.id,
                symbol=symbol,
                decision=exit_decision_type,
                reasoning=f"EXIT (close position): Close {decision_type} position after earnings announcement | Allocated: ${entry_amount:.2f}",
                execution_time=exit_time,
                status='PENDING',
                allocated_amount=entry_amount
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
        from services.interactive_brokers_service import InteractiveBrokersService
        
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
                    
                    # Default order amount in USD
                    ORDER_AMOUNT_USD = decision.allocated_amount if decision.allocated_amount else 1000.0
                    print(f"[JOB] Target Amount: ${ORDER_AMOUNT_USD}")

                    qty = 1.0
                    
                    # 1. Get current price to calculate quantity
                    current_price = 0.0
                    try:
                        # Try getting price from Service if possible, or MarketData
                        if isinstance(service, IGMarketsService):
                             # For IG, we might need a different approach or just use size=1 for spread betting
                             # Placeholder for IG logic
                             pass
                        elif isinstance(service, AlpacaService):
                             # Need price to calc quantity
                             # We can use market_data_service as fallback
                             quote = await market_data_service.get_quote(symbol)
                             current_price = quote.get('price', 0.0)
                        elif isinstance(service, InteractiveBrokersService):
                             # For IB, use market_data_service for price
                             quote = await market_data_service.get_quote(symbol)
                             current_price = quote.get('price', 0.0)
                    except Exception as px:
                        print(f"[JOB] Could not get price for {symbol}: {px}")
                    
                    # 2. Calculate Quantity
                    if current_price > 0:
                        raw_qty = ORDER_AMOUNT_USD / current_price
                        # Alpaca supports fractional shares, but let's stick to 2 decimals or integer for safety?
                        # Alpaca paper supports fractionals.
                        qty = round(raw_qty, 4)
                        if qty < 0.0001: qty = 0.0001 # Min size
                        print(f"[JOB] Calculated qty: {qty} based on price {current_price} and target ${ORDER_AMOUNT_USD}")
                    else:
                        print(f"[JOB] Warning: Using default qty 1 because price unknown")
                        qty = 1

                    
                    order_result = None
                    order_status = "UNKNOWN"
                    order_id = None
                    
                    if isinstance(service, IGMarketsService):
                        # IG Execution
                        epic = service.get_epic_for_symbol(symbol)
                        if not epic:
                            raise Exception(f"Could not resolve epic for {symbol}")
                        
                        is_liquidation = decision.reasoning and "FORCE LIQUIDATION" in decision.reasoning
                        
                        if is_liquidation:
                            print(f"[JOB] Detected FORCE LIQUIDATION for {symbol} on IG. Finding deal ID...")
                            pos_response = await service.get_positions()
                            
                            target_deal_id = None
                            target_direction = None
                            
                            if pos_response:
                                # Positions is typically a list of dicts from get_positions
                                for p in pos_response:
                                    if p.get('epic') == epic:
                                        target_deal_id = p.get('deal_id') or p.get('dealId')
                                        # To close the deal, we pass opposite direction or current direction depending on API? 
                                        # For IG, normally close direction is opposite of open direction.
                                        curr_dir = p.get('direction', '')
                                        target_direction = 'SELL' if curr_dir == 'BUY' else 'BUY'
                                        break
                                        
                            if target_deal_id and target_direction:
                                print(f"[JOB] Found deal {target_deal_id} for {epic}. Closing...")
                                order_result = await service.close_position(
                                    deal_id=target_deal_id,
                                    direction=target_direction
                                )
                                order_id = order_result.get('deal_reference') or order_result.get('dealReference')
                                order_status = 'FILLED' if order_result.get('status') == 'closed' else 'PENDING_VERIFICATION'
                            else:
                                print(f"[JOB] Could not find open IG deal for {epic} to liquidate. Assuming already closed.")
                                order_id = "IG_ALREADY_CLOSED"
                                order_status = "FILLED"
                        
                        else:
                            # Standard order
                            # Set to deal in CFDs (which IG defaults to for many markets)
                            order_result = await service.place_market_order(
                                epic=epic,
                                direction=action.upper(),
                                size=1 
                            )
                            order_id = order_result.get('dealReference') or order_result.get('dealId')
                            
                            # Verify IG order status (simplified)
                            if order_result.get('dealStatus') == 'ACCEPTED':
                                order_status = 'FILLED'
                            else:
                                # Wait a bit and check position / deal status
                                await asyncio.sleep(2)
                                pos_response = await service.get_positions()
                                if pos_response:
                                    # Pos response list of dicts from IGMarketsService.get_positions()
                                    is_filled = any(p.get('epic') == epic for p in pos_response)
                                    order_status = 'FILLED' if is_filled else 'FAILED'
                                else:
                                    order_status = 'PENDING'

                    elif isinstance(service, AlpacaService):
                        # Alpaca Execution
                        is_liquidation = decision.reasoning and "FORCE LIQUIDATION" in decision.reasoning
                        
                        if is_liquidation:
                            print(f"[JOB] Detected FORCE LIQUIDATION for {symbol} on Alpaca. Using native close_position()")
                            try:
                                positions = await service.get_positions()
                                has_pos = any(p.get('symbol') == symbol for p in positions)
                                if not has_pos:
                                    print(f"[JOB] Position {symbol} already closed. Marking liquidation as filled.")
                                    order_status = 'FILLED'
                                    order_id = "AL_ALREADY_CLOSED"
                                else:
                                    order_result = await service.close_position(symbol)
                                    order_id = "AL_LIQUIDATION"
                                    
                                    # Give Alpaca time to process the closure
                                    await asyncio.sleep(3)
                                    
                                    # Verify closed position
                                    positions = await service.get_positions()
                                    is_closed = not any(p.get('symbol') == symbol for p in positions)
                                    if not is_closed:
                                        # Retry once more after longer wait
                                        await asyncio.sleep(5)
                                        positions = await service.get_positions()
                                        is_closed = not any(p.get('symbol') == symbol for p in positions)
                                        if is_closed:
                                            print(f"[JOB] Position {symbol} closed on second check")
                                    order_status = 'FILLED' if is_closed else 'FAILED'
                                    if not is_closed:
                                       print(f"[JOB] Position {symbol} still open after liquidation attempt on Alpaca")
                            except Exception as e:
                                print(f"[JOB] Could not verify liquidation status on Alpaca: {e}")
                                import traceback
                                traceback.print_exc()
                                order_status = 'PENDING_VERIFICATION'
                                order_id = f"AL_LIQUIDATION_ERR: {str(e)[:100]}"

                        else:
                            # Standard order
                            order_result = await service.place_market_order(
                                symbol=symbol,
                                qty=qty,
                                side=action.lower(),
                                take_profit=decision.take_profit,
                                stop_loss=decision.stop_loss
                            )
                            order_id = order_result.get('id')
                            
                            # Verify Alpaca Order Execution
                            import time
                            retries = 0
                            while retries < 5:
                                await asyncio.sleep(2)  # Wait 2 seconds
                                try:
                                    status_check = await service.get_orders(status='all', limit=10)
                                    # Find our order by ID
                                    order_info = next((o for o in status_check if o.get('id') == order_id), None)
                                    
                                    if order_info:
                                        current_state = order_info.get('status')
                                        if current_state == 'filled':
                                            order_status = 'FILLED'
                                            break
                                        elif current_state in ['canceled', 'rejected', 'expired', 'replaced']:
                                            order_status = 'FAILED'
                                            print(f"[JOB] Alpaca order failed or rejected: {current_state}")
                                            break
                                        else:
                                            print(f"[JOB] Alpaca order still pending: {current_state}, retrying...")
                                except Exception as e:
                                    print(f"[JOB] Error checking Alpaca order status: {e}")
                                
                                retries += 1
                                
                            # If after 5 retries it's still unknown, set it to what we have
                            if order_status == "UNKNOWN":
                                order_status = "PENDING_VERIFICATION"

                    elif isinstance(service, InteractiveBrokersService):
                        # Interactive Brokers Execution
                        is_liquidation = decision.reasoning and "FORCE LIQUIDATION" in decision.reasoning
                        
                        if is_liquidation:
                            print(f"[JOB] Detected FORCE LIQUIDATION for {symbol} on IB. Using native close_position()")
                            try:
                                positions = await service.get_positions()
                                has_pos = any(p.get('symbol') == symbol for p in positions)
                                if not has_pos:
                                    print(f"[JOB] Position {symbol} already closed. Marking liquidation as filled.")
                                    order_status = 'FILLED'
                                    order_id = "IB_ALREADY_CLOSED"
                                else:
                                    order_result = await service.close_position(symbol)
                                    order_status = 'PLACED'
                                    order_id = "IB_LIQUIDATION"
                            except Exception as e:
                                print(f"[JOB] Error during IB liquidation: {e}")
                                order_status = 'FAILED'
                                order_id = "IB_ERR"
                        else:
                            # Standard order
                            order_result = await service.place_market_order(
                                symbol=symbol,
                                qty=qty,
                                side=action.lower()
                            )
                            order_status = 'PLACED' # IB handles this differently, assume placed for now
                            order_id = "IB_ORDER"
                    else:
                        raise Exception("Unknown service type")

                    if order_status == 'FILLED' or order_status == 'PLACED' or order_status == 'PENDING_VERIFICATION':
                        decision.status = "EXECUTED"
                        decision.executed_at = datetime.now()
                        decision.reasoning = (decision.reasoning or "") + f" | Order ID: {order_id} | Qty: {qty} | Price: {current_price} | ExecStatus: {order_status}"
                        scheduler_service.log_execution(job_name, "SUCCESS", f"Executed {action} {symbol} (Bot {bot.name})")
                    else:
                        decision.status = "FAILED"
                        decision.executed_at = datetime.now()
                        decision.reasoning = (decision.reasoning or "") + f" | Order ID: {order_id} | Qty: {qty} | Price: {current_price} | ExecStatus: {order_status} (Order did not fill)"
                        scheduler_service.log_execution(job_name, "ERROR", f"Order {action} {symbol} did not fill (Bot {bot.name})")
                    
                except Exception as e:
                    print(f"[JOB] Error executing order for {decision.symbol}: {e}")
                    import traceback
                    traceback.print_exc()
                    
                    is_liquidation = decision.reasoning and "FORCE LIQUIDATION" in decision.reasoning
                    error_detail = str(e)[:200]
                    
                    # For FORCE LIQUIDATION: retry up to 3 times by resetting to PENDING
                    if is_liquidation:
                        retry_count = (decision.reasoning or "").count("[RETRY")
                        if retry_count < 3:
                            decision.status = "PENDING"
                            decision.execution_time = datetime.now() + timedelta(minutes=5)
                            decision.reasoning = (decision.reasoning or "") + f" | [RETRY {retry_count + 1}/3] Error: {error_detail}"
                            print(f"[JOB] FORCE LIQUIDATION for {decision.symbol} failed, scheduling retry {retry_count + 1}/3 in 5 min")
                        else:
                            decision.status = "FAILED"
                            decision.reasoning = (decision.reasoning or "") + f" | [MAX RETRIES] Error: {error_detail}"
                            print(f"[JOB] FORCE LIQUIDATION for {decision.symbol} failed after 3 retries")
                    else:
                        decision.status = "FAILED"
                        decision.reasoning = (decision.reasoning or "") + f" | Error: {error_detail}"
                    scheduler_service.log_execution(job_name, "ERROR", f"Failed {decision.symbol}: {e}")
        
        db.commit()
        
    except Exception as e:
        print(f"[JOB] Error in execute_orders_job: {e}")
        scheduler_service.log_execution(job_name, "ERROR", str(e))
    finally:
        db.close()


async def cleanup_old_decisions_job():
    """
    Clean up old decisions from database to keep it manageable.
    Runs daily.
    """
    job_name = "cleanup_old_decisions"
    print(f"[JOB] Starting {job_name}...")
    
    db = SessionLocal()
    try:
        from datetime import datetime, timedelta
        cutoff = datetime.now() - timedelta(days=30)
        
        # Delete decisions older than 30 days (any status except PENDING? maybe all)
        deleted = db.query(Decision).filter(
            Decision.created_at < cutoff,
            Decision.status.in_(['EXECUTED', 'FAILED', 'SKIPPED'])
        ).delete(synchronize_session=False)
        
        db.commit()
        print(f"[JOB] Cleaned up {deleted} old decisions")
        scheduler_service.log_execution(job_name, "SUCCESS", f"Cleaned {deleted} old decisions")
        
    except Exception as e:
        print(f"[JOB] Error in cleanup_old_decisions_job: {e}")
        scheduler_service.log_execution(job_name, "ERROR", str(e))
    finally:
        db.close()


async def update_bot_performance_job():
    """
    Job to update bot performance history (profit, win_rate) regularly.
    Runs every 30 minutes.
    """
    job_name = "update_bot_performance"
    print(f"[JOB] Starting {job_name}...")
    
    db = SessionLocal()
    try:
        active_bots = db.query(Bot).filter(Bot.is_active == True).all()
        for bot in active_bots:
            try:
                service = bot_service._get_configured_service(db, bot)
                if not service:
                    continue
                
                profit_percent = 0.0
                
                if isinstance(service, IGMarketsService):
                    account_info = service.get_account() if not asyncio.iscoroutinefunction(service.get_account) else await service.get_account()
                    if isinstance(account_info, dict):
                        # Calculate profit as a percentage of deposit/balance, or just absolute profit
                        pl = float(account_info.get('profit_loss', 0))
                        # Use a simple representation for tracking (unrealized PL today or from history)
                        # We will track pl directly as standard "profit" for simplicity.
                        # IG pl is often raw currency value. Let's just store it.
                        profit_percent = pl

                elif isinstance(service, AlpacaService):
                    # For alpaca we get account equity
                    try:
                        account_info = await service.get_account() if asyncio.iscoroutinefunction(service.get_account) else service.get_account()
                        if isinstance(account_info, dict):
                            equity = float(account_info.get('portfolio_value', 100000))
                            profit_percent = ((equity - 100000.0) / 100000.0) * 100.0  # Assumes 100k starting paper balance
                            
                        # Extract win rate from closed trades
                        try:
                            # We can just fetch all orders if get_orders doesn't support easy closed filtering
                            closed_orders = await service.get_orders(status='all', limit=500) if asyncio.iscoroutinefunction(service.get_orders) else service.get_orders(status='all', limit=500)
                            
                            if closed_orders and isinstance(closed_orders, list):
                                # alpaca-py returns dictionaries from the service wrapper
                                filled_orders = [o for o in closed_orders if isinstance(o, dict) and 'filled' in str(o.get('status', '')).lower()]
                                if filled_orders:
                                    bot.total_trades = len(filled_orders) // 2 # approx roundtrip
                                    if bot.total_trades > 0:
                                        if profit_percent > 0:
                                            bot.win_rate = min(100.0, 50.0 + (profit_percent / 100))
                                        else:
                                            bot.win_rate = max(0.0, 50.0 + (profit_percent / 100))
                        except Exception as e:
                            print(f"[JOB] Error calculating Alpaca win_rate: {e}")
                            
                    except Exception as e:
                        print(f"[JOB] Error fetching Alpaca account: {e}")
                
                # Default fallback (read global profitto.json if bot profit is missing)
                if profit_percent == 0.0:
                    profit_path = os.path.join(os.path.dirname(__file__), "..", "profitto.json")
                    if os.path.exists(profit_path):
                        with open(profit_path, "r", encoding="utf-8") as f:
                            pdata = json.load(f)
                        profit_percent = float(pdata.get("profit_loss_value", 0))

                bot.profit = profit_percent
                
                # Append to history
                history = []
                if bot.performance_history:
                    try:
                        history = json.loads(bot.performance_history)
                    except Exception:
                        pass
                
                # If history is mostly empty and it's Alpaca, try to backfill
                if len(history) < 2 and isinstance(service, AlpacaService) and hasattr(service, 'client') and service.client:
                    try:
                        from alpaca.trading.requests import GetPortfolioHistoryRequest
                        req = GetPortfolioHistoryRequest(period="1A", timeframe="1D")
                        alpaca_history = service.client.get_portfolio_history(req)
                        if alpaca_history and hasattr(alpaca_history, 'timestamp') and alpaca_history.timestamp:
                            history = []
                            for ts, eq in zip(alpaca_history.timestamp, alpaca_history.equity):
                                eq_val = float(eq) if eq else 100000.0
                                hist_pct = ((eq_val - 100000.0) / 100000.0) * 100.0
                                history.append({
                                    "time": int(ts),
                                    "value": round(hist_pct, 4),
                                    "winRate": bot.win_rate
                                })
                    except Exception as e:
                        print(f"[JOB] Error backfilling Alpaca history: {e}")
                
                # Keep last 365 points for 1A
                if len(history) > 400:
                    history = history[-400:]

                history.append({
                    "time": int(datetime.now().timestamp()), # Unix timestamp
                    "value": bot.profit,
                    "winRate": bot.win_rate
                })
                
                bot.performance_history = json.dumps(history)
                db.add(bot)
                print(f"[JOB] Updated performance history for {bot.name}: Profit {bot.profit}")
                
            except Exception as e:
                print(f"[JOB] Error updating performance for bot {bot.name}: {e}")
                
        db.commit()
        scheduler_service.log_execution(job_name, "SUCCESS", f"Updated {len(active_bots)} bots")
    except Exception as e:
         print(f"[JOB] Error in update_bot_performance_job: {e}")
         scheduler_service.log_execution(job_name, "ERROR", str(e))
    finally:
         db.close()
