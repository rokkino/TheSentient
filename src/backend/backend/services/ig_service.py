"""
IG Markets Trading Service
Handles integration with IG Markets API using trading-ig
"""
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

try:
    from trading_ig import IGService as TradingIGService, IGStreamService
    from trading_ig.lightstreamer import Subscription
    IG_AVAILABLE = True
except ImportError:
    IG_AVAILABLE = False
    print("Warning: trading-ig not installed. Install it with: pip install trading-ig")

class IGMarketsService:
    def __init__(self, username: Optional[str] = None, password: Optional[str] = None, api_key: Optional[str] = None, acc_type: str = "DEMO"):
        """
        Initialize IG Markets service
        
        Args:
            username: IG username (default: rokkino96)
            password: IG password
            api_key: IG API key (required)
            acc_type: Account type - "DEMO" or "LIVE"
        """
        # Use provided credentials or fallback to environment variables
        self.username = username or os.getenv('IG_USERNAME')
        self.password = password or os.getenv('IG_PASSWORD')
        self.api_key = api_key or os.getenv('IG_API_KEY')
        self.acc_type = acc_type or os.getenv('IG_ACC_TYPE', 'DEMO')
        
        self.ig_service = None
        self.stream_service = None
        self.cst = None  # Client session token
        self.x_security_token = None
        
        if not IG_AVAILABLE:
            print("IG library not available. Install trading-ig to use trading features.")
            return
        
        if not self.api_key:
            print("Warning: IG API key not provided. Set IG_API_KEY environment variable.")
            return
        
        # Initialize IG service
        try:
            self.ig_service = TradingIGService(
                username=self.username,
                password=self.password,
                api_key=self.api_key,
                acc_type=self.acc_type
            )
            # Login to get session tokens
            response = self.ig_service.create_session()
            if response:
                # Extract tokens from response (structure may vary)
                if hasattr(response, 'headers'):
                    self.cst = response.headers.get('CST', '')
                    self.x_security_token = response.headers.get('X-SECURITY-TOKEN', '')
                elif isinstance(response, dict):
                    self.cst = response.get('CST', '')
                    self.x_security_token = response.get('X-SECURITY-TOKEN', '')
                print(f"[IG] Successfully connected to {self.acc_type} account")
        except Exception as e:
            print(f"[IG] Error initializing IG service: {e}")
            import traceback
            traceback.print_exc()
            self.ig_service = None
    
    def is_configured(self) -> bool:
        """Check if IG service is configured"""
        if not IG_AVAILABLE:
            return False
        return self.ig_service is not None and self.cst is not None
    
    async def get_account(self) -> Dict[str, Any]:
        """Get account information"""
        if not IG_AVAILABLE:
            raise ValueError("trading-ig not installed. Install it with: pip install trading-ig")
        if not self.is_configured():
            raise ValueError("IG service not configured. Please set IG_API_KEY, IG_USERNAME, IG_PASSWORD")
        
        try:
            accounts = self.ig_service.fetch_accounts()
            if accounts:
                account = accounts[0]  # Get primary account
                return {
                    "account_id": account.get('accountId', ''),
                    "account_name": account.get('accountName', ''),
                    "account_type": account.get('accountType', ''),
                    "currency": account.get('currency', 'USD'),
                    "balance": float(account.get('balance', {}).get('balance', 0)),
                    "available": float(account.get('balance', {}).get('available', 0)),
                    "deposit": float(account.get('balance', {}).get('deposit', 0)),
                    "profit_loss": float(account.get('balance', {}).get('profitLoss', 0)),
                    "account_status": account.get('status', ''),
                }
            return {}
        except Exception as e:
            raise Exception(f"Failed to get account: {str(e)}")
    
    async def get_positions(self) -> List[Dict[str, Any]]:
        """Get all open positions"""
        if not IG_AVAILABLE:
            raise ValueError("trading-ig not installed")
        if not self.is_configured():
            raise ValueError("IG service not configured")
        
        try:
            positions_response = self.ig_service.fetch_open_positions()
            result = []
            
            # Handle different response formats
            positions = []
            if isinstance(positions_response, dict):
                positions = positions_response.get('positions', [])
            elif isinstance(positions_response, list):
                positions = positions_response
            else:
                # Try to access as attribute
                positions = getattr(positions_response, 'positions', [])
            
            for pos in positions:
                # Handle both dict and object responses
                if isinstance(pos, dict):
                    deal_id = pos.get('dealId', pos.get('deal_id', ''))
                    epic = pos.get('epic', '')
                    direction = pos.get('direction', '')
                    size = pos.get('size', 0)
                else:
                    deal_id = getattr(pos, 'dealId', getattr(pos, 'deal_id', ''))
                    epic = getattr(pos, 'epic', '')
                    direction = getattr(pos, 'direction', '')
                    size = getattr(pos, 'size', 0)
                
                result.append({
                    "deal_id": deal_id,
                    "epic": epic,
                    "direction": direction,
                    "size": float(size) if size else 0,
                })
            return result
        except Exception as e:
            raise Exception(f"Failed to get positions: {str(e)}")
    
    async def get_orders(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get orders"""
        if not IG_AVAILABLE:
            raise ValueError("trading-ig not installed")
        if not self.is_configured():
            raise ValueError("IG service not configured")
        
        try:
            if status == 'open':
                working_orders = self.ig_service.fetch_working_orders()
                return [
                    {
                        "deal_id": order.get('dealId', ''),
                        "epic": order.get('epic', ''),
                        "instrument_name": order.get('instrumentName', ''),
                        "direction": order.get('direction', ''),
                        "size": float(order.get('size', 0)),
                        "order_type": order.get('orderType', ''),
                        "level": float(order.get('level', 0)),
                        "time_in_force": order.get('timeInForce', ''),
                        "status": order.get('status', ''),
                    }
                    for order in working_orders
                ]
            return []
        except Exception as e:
            raise Exception(f"Failed to get orders: {str(e)}")
    
    async def place_market_order(self, epic: str, direction: str, size: float, 
                                 stop_level: Optional[float] = None, 
                                 limit_level: Optional[float] = None) -> Dict[str, Any]:
        """
        Place a market order
        
        Args:
            epic: Instrument epic (e.g., 'IX.D.SPTRD.IFM.IP' for S&P 500)
            direction: 'BUY' or 'SELL'
            size: Size of the position (in units)
            stop_level: Optional stop loss level
            limit_level: Optional take profit level
        
        Returns:
            Order details
        """
        if not IG_AVAILABLE:
            raise ValueError("trading-ig not installed")
        if not self.is_configured():
            raise ValueError("IG service not configured")
        
        try:
            # Create market order
            response = self.ig_service.create_open_position(
                epic=epic,
                direction=direction,
                size=size,
                order_type='MARKET',
                stop_level=stop_level,
                limit_level=limit_level,
                time_in_force='FILL_OR_KILL'
            )
            
            if response:
                # Handle response (can be dict or object)
                if isinstance(response, dict):
                    deal_ref = response.get('dealReference', response.get('deal_reference', ''))
                else:
                    deal_ref = getattr(response, 'dealReference', getattr(response, 'deal_reference', ''))
                
                # Fetch deal status to get deal ID
                try:
                    deal_status = self.ig_service.fetch_deal_by_deal_reference(deal_ref)
                    if isinstance(deal_status, dict):
                        deal_id = deal_status.get('dealId', deal_status.get('deal_id', ''))
                        status = deal_status.get('status', '')
                    else:
                        deal_id = getattr(deal_status, 'dealId', getattr(deal_status, 'deal_id', ''))
                        status = getattr(deal_status, 'status', '')
                except:
                    deal_id = ''
                    status = 'accepted'
                
                return {
                    "deal_reference": deal_ref,
                    "deal_id": deal_id,
                    "status": status,
                    "epic": epic,
                    "direction": direction,
                    "size": size,
                }
            
            raise Exception("No response from IG API")
            
        except Exception as e:
            raise Exception(f"Failed to place order: {str(e)}")
    
    async def close_position(self, deal_id: str, direction: str, size: Optional[float] = None) -> Dict[str, Any]:
        """Close a position"""
        if not IG_AVAILABLE:
            raise ValueError("trading-ig not installed")
        if not self.is_configured():
            raise ValueError("IG service not configured")
        
        try:
            response = self.ig_service.close_open_position(
                deal_id=deal_id,
                direction=direction,
                size=size  # None means close entire position
            )
            
            if response:
                if isinstance(response, dict):
                    deal_ref = response.get('dealReference', response.get('deal_reference', ''))
                else:
                    deal_ref = getattr(response, 'dealReference', getattr(response, 'deal_reference', ''))
                
                return {
                    "deal_reference": deal_ref,
                    "deal_id": deal_id,
                    "status": "closed"
                }
            
            raise Exception("No response from IG API")
            
        except Exception as e:
            raise Exception(f"Failed to close position: {str(e)}")
    
    async def search_markets(self, search_term: str) -> List[Dict[str, Any]]:
        """Search for markets/instruments"""
        if not IG_AVAILABLE:
            raise ValueError("trading-ig not installed")
        if not self.is_configured():
            raise ValueError("IG service not configured")
        
        try:
            markets_response = self.ig_service.search_markets(search_term)
            
            # Handle different response formats
            markets = []
            if isinstance(markets_response, dict):
                markets = markets_response.get('markets', [])
            elif isinstance(markets_response, list):
                markets = markets_response
            else:
                markets = getattr(markets_response, 'markets', [])
            
            result = []
            for market in markets:
                if isinstance(market, dict):
                    epic = market.get('epic', '')
                    instrument_name = market.get('instrumentName', market.get('instrument_name', ''))
                else:
                    epic = getattr(market, 'epic', '')
                    instrument_name = getattr(market, 'instrumentName', getattr(market, 'instrument_name', ''))
                
                if epic:
                    result.append({
                        "epic": epic,
                        "instrument_name": instrument_name,
                        "instrument_type": market.get('instrumentType', '') if isinstance(market, dict) else getattr(market, 'instrumentType', ''),
                        "expiry": market.get('expiry', '') if isinstance(market, dict) else getattr(market, 'expiry', ''),
                        "market_status": market.get('marketStatus', '') if isinstance(market, dict) else getattr(market, 'marketStatus', ''),
                    })
            return result
        except Exception as e:
            raise Exception(f"Failed to search markets: {str(e)}")
    
    def get_epic_for_symbol(self, symbol: str) -> Optional[str]:
        """
        Get IG epic for a stock symbol
        IG Markets uses epics like 'IX.D.SPTRD.IFM.IP' for indices
        For individual stocks CFD, format is typically: 'UA.D.{SYMBOL}.CFD.IP' for US stocks
        """
        symbol_upper = symbol.upper()
        
        # Common mappings for indices
        epic_mappings = {
            'SPY': 'IX.D.SPTRD.IFM.IP',  # S&P 500 Index
            'QQQ': 'IX.D.NASDAQ.IFM.IP',  # NASDAQ Index
            'DIA': 'IX.D.DOW.IFM.IP',  # Dow Jones Index
            '^GSPC': 'IX.D.SPTRD.IFM.IP',  # S&P 500
            '^IXIC': 'IX.D.NASDAQ.IFM.IP',  # NASDAQ
            '^DJI': 'IX.D.DOW.IFM.IP',  # Dow Jones
        }
        
        if symbol_upper in epic_mappings:
            return epic_mappings[symbol_upper]
        
        # For individual stocks, try CFD format
        # Format: UA.D.{SYMBOL}.CFD.IP (US stocks CFD)
        # Note: This may not work for all stocks - search_markets should be used for verification
        return f'UA.D.{symbol_upper}.CFD.IP'
    
    async def get_market_info(self, epic: str) -> Dict[str, Any]:
        """Get market information for an epic"""
        if not IG_AVAILABLE:
            raise ValueError("trading-ig not installed")
        if not self.is_configured():
            raise ValueError("IG service not configured")
        
        try:
            market_response = self.ig_service.fetch_market_by_epic(epic)
            
            if market_response:
                # Handle different response formats
                if isinstance(market_response, dict):
                    market = market_response
                    snapshot = market.get('snapshot', {})
                else:
                    market = market_response
                    snapshot = getattr(market, 'snapshot', {})
                
                # Extract data safely
                if isinstance(snapshot, dict):
                    bid = float(snapshot.get('bid', 0))
                    offer = float(snapshot.get('offer', 0))
                else:
                    bid = float(getattr(snapshot, 'bid', 0))
                    offer = float(getattr(snapshot, 'offer', 0))
                
                if isinstance(market, dict):
                    instrument_name = market.get('instrumentName', market.get('instrument_name', ''))
                else:
                    instrument_name = getattr(market, 'instrumentName', getattr(market, 'instrument_name', ''))
                
                return {
                    "epic": epic,
                    "instrument_name": instrument_name,
                    "bid": bid,
                    "offer": offer,
                    "current_price": (bid + offer) / 2 if bid and offer else bid or offer,
                }
            return {}
        except Exception as e:
            raise Exception(f"Failed to get market info: {str(e)}")
