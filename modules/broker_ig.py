from trading_ig import IGService
from trading_ig.rest import IGException
from config import IG_USERNAME, IG_PASSWORD, IG_API_KEY, IG_ACC_TYPE, IG_ACC_NUMBER, MAX_SPREAD_PIPS
from .utils import setup_logger

logger = setup_logger("BrokerIG")

class IGBroker:
    def __init__(self):
        self.ig_service = IGService(IG_USERNAME, IG_PASSWORD, IG_API_KEY, acc_type=IG_ACC_TYPE)
        self.session = None

    def login(self):
        """
        Logs in to IG Markets.
        """
        try:
            self.ig_service.create_session()
            self.session = self.ig_service.fetch_session_details()
            logger.info(f"Logged in to IG Markets ({IG_ACC_TYPE}). Account: {IG_ACC_NUMBER}")
            return True
        except IGException as e:
            logger.error(f"IG Login Failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during login: {e}")
            return False

    def get_open_positions(self):
        """
        Fetches open positions.
        """
        try:
            positions = self.ig_service.fetch_open_positions()
            return positions
        except Exception as e:
            logger.error(f"Error fetching positions: {e}")
            return []

    def place_order(self, ticker: str, direction: str, size: float, stop_loss: float, take_profit: float):
        """
        Places a trade order.
        """
        try:
            # 1. Check Spread
            # Need to find the epic for the ticker. This is tricky as yfinance tickers != IG epics.
            # For this simplified version, we assume the 'ticker' passed is actually the IG EPIC or we have a mapping.
            # Let's assume the Analyst provides the IG EPIC or a common symbol we can search.
            
            # Search for the epic if needed (omitted for brevity, assuming ticker IS epic or we search)
            epic = ticker 
            
            market_info = self.ig_service.fetch_market_by_epic(epic)
            if not market_info:
                logger.error(f"Market not found for epic: {epic}")
                return False
                
            bid = market_info.snapshot.bid
            offer = market_info.snapshot.offer
            spread = offer - bid
            
            # Check spread (simplified, pips calculation depends on instrument)
            # Assuming spread is in points for now
            if spread > MAX_SPREAD_PIPS:
                 logger.warning(f"Spread too high ({spread} > {MAX_SPREAD_PIPS}). Skipping trade.")
                 return False

            # 2. Place Order
            currency_code = 'USD' # Should be dynamic
            
            response = self.ig_service.create_open_position(
                currency_code=currency_code,
                direction=direction,
                epic=epic,
                expiry='DFB', # Daily Funded Bet
                force_open=True,
                guaranteed_stop=False,
                level=None, # Market order
                limit_distance=None,
                limit_level=take_profit,
                order_type='MARKET',
                quote_id=None,
                size=size,
                stop_distance=None,
                stop_level=stop_loss
            )
            
            logger.info(f"Order Placed: {response}")
            return True

        except IGException as e:
            logger.error(f"IG Order Failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error placing order: {e}")
            return False
