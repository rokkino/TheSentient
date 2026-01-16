import time
import sys
from datetime import datetime
import pytz

from config import SLEEP_INTERVAL_SECONDS
from modules.utils import setup_logger
from modules.market_data import get_market_data, is_market_open
from modules.manager_ai import consult_manager
from modules.analyst_ai import analyze_opportunity
from modules.broker_ig import IGBroker

logger = setup_logger("Main")

def main():
    logger.info("Starting Hybrid AI Trading Bot...")
    
    # Initialize Broker
    broker = IGBroker()
    if not broker.login():
        logger.error("Failed to login to IG Markets. Exiting.")
        return # Exit if login fails

    # Main Loop
    try:
        while True:
            try:
                # 1. Get Time & Status
                rome_tz = pytz.timezone('Europe/Rome')
                now = datetime.now(rome_tz)
                current_time_str = now.strftime("%Y-%m-%d %H:%M:%S %Z")
                
                market_status = "OPEN" if is_market_open() else "CLOSED"
                
                # 2. Consult Manager AI (Ollama)
                open_positions = broker.get_open_positions()
                manager_decision = consult_manager(current_time_str, market_status, open_positions)
                
                action = manager_decision.get("action", "SLEEP")
                logger.info(f"Manager Decision: {action}")
                
                if action == "ACTIVATE_ANALYST":
                    context = manager_decision.get("context", "")
                    
                    # For this example, we iterate through a watchlist or specific ticker from context
                    # If context is "CHECK_STOPS", we might look at open positions.
                    # If context implies a new trade, we look at a watchlist.
                    # Simplified: Let's assume we watch 'SPY' (or the equivalent IG Epic)
                    ticker = "SPY" 
                    
                    # 3. Fetch Data
                    logger.info(f"Fetching data for {ticker}...")
                    market_data = get_market_data(ticker)
                    
                    # 4. Consult Analyst AI (Gemini)
                    analyst_decision = analyze_opportunity(ticker, market_data, news_summary=context)
                    
                    decision = analyst_decision.get("decision", "PASS")
                    logger.info(f"Analyst Decision: {decision}")
                    
                    if decision in ["BUY", "SELL"]:
                        # 5. Execute Trade
                        # Extract parameters
                        entry_price = analyst_decision.get("entry_price")
                        stop_loss = analyst_decision.get("stop_loss")
                        take_profit = analyst_decision.get("take_profit")
                        size = analyst_decision.get("size", 1)
                        
                        logger.info(f"Executing {decision} on {ticker}...")
                        broker.place_order(ticker, decision, size, stop_loss, take_profit)
                        
                elif action == "SLEEP":
                    pass
                else:
                    logger.warning(f"Unknown Manager action: {action}")

            except Exception as e:
                logger.error(f"Error in main loop: {e}")
            
            # Sleep
            logger.info(f"Sleeping for {SLEEP_INTERVAL_SECONDS} seconds...")
            time.sleep(SLEEP_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
    except Exception as e:
        logger.critical(f"Critical error: {e}")

if __name__ == "__main__":
    main()
