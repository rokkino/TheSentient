"""
Alpaca Paper Trading Service
Handles integration with Alpaca Markets API for paper trading
"""
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

# Try to import Alpaca libraries (alpaca-py: use alpaca.trading, not alpaca.trade)
try:
    from alpaca.trading.client import TradingClient
    from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest, GetOrdersRequest, GetAssetsRequest
    from alpaca.trading.enums import OrderSide, TimeInForce, OrderType, AssetClass, AssetStatus
    from alpaca.data.historical import StockHistoricalDataClient
    from alpaca.data.requests import StockBarsRequest
    from alpaca.data.timeframe import TimeFrame
    ALPACA_AVAILABLE = True
except ImportError:
    ALPACA_AVAILABLE = False
    # Silently fail - Alpaca is optional, we use IG Markets now
    pass

from services.symbol_mapper import symbol_mapper

class AlpacaService:
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None, paper: bool = True):
        global ALPACA_AVAILABLE
        # Get API keys from arguments or environment variables
        self.api_key = api_key or os.getenv('ALPACA_API_KEY', '')
        self.api_secret = api_secret or os.getenv('ALPACA_API_SECRET', '')
        
        # Determine base URL
        if paper:
            self.base_url = os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets')
        else:
            self.base_url = 'https://api.alpaca.markets'
            
        self.client = None
        self.data_client = None
        self.init_error = None
        
        # If global import failed, try again here to capture the error
        if not ALPACA_AVAILABLE:
            try:
                from alpaca.trading.client import TradingClient
                ALPACA_AVAILABLE = True
            except ImportError as e:
                self.init_error = f"Library Import Error: {str(e)}"
                print(f"[ALPACA] Import error: {e}")
                return
            except Exception as e:
                self.init_error = f"Library Init Error: {str(e)}"
                print(f"[ALPACA] Init error: {e}")
                return
        
        self.init_error = None
        
        if self.api_key and self.api_secret:
            try:
                from alpaca.trading.client import TradingClient
                from alpaca.data.historical import StockHistoricalDataClient
                
                self.client = TradingClient(
                    api_key=self.api_key,
                    secret_key=self.api_secret,
                    paper=paper,
                    url_override=self.base_url
                )
                self.data_client = StockHistoricalDataClient(
                    api_key=self.api_key,
                    secret_key=self.api_secret
                )
            except Exception as e:
                print(f"Error initializing Alpaca client: {e}")
                self.init_error = str(e)
                pass
    
    def is_configured(self) -> bool:
        """Check if Alpaca API is configured"""
        if not ALPACA_AVAILABLE:
            return False
        return self.client is not None and self.data_client is not None
    
    async def get_account(self) -> Dict[str, Any]:
        """Get account information"""
        if not ALPACA_AVAILABLE:
            raise ValueError("Alpaca library not installed. Install it with: pip install alpaca-py")
            
        # Relaxed check: Only need trade client for account info
        if not self.client:
            raise ValueError("Alpaca API not configured. Please set ALPACA_API_KEY and ALPACA_API_SECRET environment variables.")
        
        try:
            account = self.client.get_account()
            return {
                "account_number": account.account_number,
                "status": account.status,
                "currency": account.currency,
                "buying_power": float(account.buying_power),
                "cash": float(account.cash),
                "portfolio_value": float(account.portfolio_value),
                "pattern_day_trader": account.pattern_day_trader,
                "trading_blocked": account.trading_blocked,
                "transfers_blocked": account.transfers_blocked,
                "account_blocked": account.account_blocked,
                "created_at": account.created_at.isoformat() if getattr(account, 'created_at', None) else None,
                "trade_suspended_by_user": account.trade_suspended_by_user,
                "multiplier": float(account.multiplier) if hasattr(account, 'multiplier') else 1.0,
                "equity": float(account.equity) if hasattr(account, 'equity') else float(account.portfolio_value),
            }
        except Exception as e:
            raise Exception(f"Failed to get account: {str(e)}")
    
    async def get_positions(self) -> List[Dict[str, Any]]:
        """Get all open positions"""
        if not ALPACA_AVAILABLE:
            raise ValueError("Alpaca library not installed. Install it with: pip install alpaca-py")
        if not self.is_configured():
            raise ValueError("Alpaca API not configured")
        
        try:
            positions = self.client.get_all_positions()
            return [
                {
                    "symbol": pos.symbol,
                    "qty": float(pos.qty),
                    "side": str(pos.side) if hasattr(pos.side, 'value') else pos.side,
                    "market_value": float(pos.market_value),
                    "cost_basis": float(pos.cost_basis),
                    "unrealized_pl": float(pos.unrealized_pl),
                    "unrealized_plpc": float(pos.unrealized_plpc),
                    "current_price": float(pos.current_price),
                    "lastday_price": float(pos.lastday_price),
                    "change_today": float(pos.change_today),
                }
                for pos in positions
            ]
        except Exception as e:
            raise Exception(f"Failed to get positions: {str(e)}")
    
    async def get_orders(self, status: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get orders (optionally filtered by status: open, closed, all)"""
        if not ALPACA_AVAILABLE:
            raise ValueError("Alpaca library not installed. Install it with: pip install alpaca-py")
        if not self.is_configured():
            raise ValueError("Alpaca API not configured")
        
        try:
            req = GetOrdersRequest(limit=limit)
            if status:
                req = GetOrdersRequest(status=status, limit=limit)
            orders = self.client.get_orders(filter=req)
            
            return [
                {
                    "id": str(order.id),
                    "symbol": order.symbol,
                    "qty": float(order.qty) if order.qty else 0,
                    "side": str(order.side) if hasattr(order.side, 'value') else order.side,
                    "type": str(getattr(order, 'order_type', order.type) or order.type),
                    "time_in_force": str(order.time_in_force) if hasattr(order.time_in_force, 'value') else order.time_in_force,
                    "status": str(order.status) if hasattr(order.status, 'value') else order.status,
                    "filled_qty": float(order.filled_qty) if order.filled_qty else 0,
                    "filled_avg_price": float(order.filled_avg_price) if order.filled_avg_price else None,
                    "limit_price": float(order.limit_price) if order.limit_price else None,
                    "stop_price": float(order.stop_price) if order.stop_price else None,
                    "submitted_at": order.submitted_at.isoformat() if order.submitted_at else None,
                    "filled_at": order.filled_at.isoformat() if order.filled_at else None,
                }
                for order in orders
            ]
        except Exception as e:
            raise Exception(f"Failed to get orders: {str(e)}")
    
    async def place_market_order(self, symbol: str, qty: float, side: str, 
                                 take_profit: Optional[float] = None, 
                                 stop_loss: Optional[float] = None) -> Dict[str, Any]:
        """Place a market order (with optional bracket TP/SL)"""
        if not ALPACA_AVAILABLE:
            raise ValueError("Alpaca library not installed. Install it with: pip install alpaca-py")
        if not self.is_configured():
            raise ValueError("Alpaca API not configured")
        
        try:
            from alpaca.trading.requests import TakeProfitRequest, StopLossRequest
            
            tp_request = TakeProfitRequest(limit_price=take_profit) if take_profit else None
            sl_request = StopLossRequest(stop_price=stop_loss) if stop_loss else None
            
            # Alpaca API specifies standard bracket parameters
            order_data = MarketOrderRequest(
                symbol=symbol,
                qty=qty,
                side=OrderSide.BUY if side.lower() == 'buy' else OrderSide.SELL,
                type=OrderType.MARKET,
                time_in_force=TimeInForce.DAY,
                take_profit=tp_request,
                stop_loss=sl_request
            )
            order = self.client.submit_order(order_data=order_data)
            return {
                "id": str(order.id),
                "symbol": order.symbol,
                "qty": float(order.qty) if order.qty else 0,
                "side": str(order.side) if hasattr(order.side, 'value') else order.side,
                "type": str(getattr(order, 'order_type', order.type) or order.type),
                "status": str(order.status) if hasattr(order.status, 'value') else order.status,
            }
        except Exception as e:
            err = str(e).lower()
            if "unauthorized" in err or "401" in err or "invalid" in err and "key" in err:
                raise Exception(
                    "Alpaca API: credenziali non valide o non autorizzate. "
                    "Verifica API Key e Secret nel profilo del bot (Paper/Live) e che l'account Alpaca sia attivo."
                )
            raise Exception(f"Failed to place order: {str(e)}")
    
    async def place_limit_order(self, symbol: str, qty: float, side: str, limit_price: float) -> Dict[str, Any]:
        """Place a limit order"""
        if not ALPACA_AVAILABLE:
            raise ValueError("Alpaca library not installed. Install it with: pip install alpaca-py")
        if not self.is_configured():
            raise ValueError("Alpaca API not configured")
        
        try:
            order_data = LimitOrderRequest(
                symbol=symbol,
                qty=qty,
                side=OrderSide.BUY if side.lower() == 'buy' else OrderSide.SELL,
                type=OrderType.LIMIT,
                time_in_force=TimeInForce.DAY,
                limit_price=limit_price
            )
            order = self.client.submit_order(order_data=order_data)
            return {
                "id": str(order.id),
                "symbol": order.symbol,
                "qty": float(order.qty) if order.qty else 0,
                "side": str(order.side) if hasattr(order.side, 'value') else order.side,
                "type": str(getattr(order, 'order_type', order.type) or order.type),
                "limit_price": float(order.limit_price) if order.limit_price else None,
                "status": str(order.status) if hasattr(order.status, 'value') else order.status,
            }
        except Exception as e:
            raise Exception(f"Failed to place limit order: {str(e)}")
    
    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel an order"""
        if not ALPACA_AVAILABLE:
            raise ValueError("Alpaca library not installed. Install it with: pip install alpaca-py")
        if not self.is_configured():
            raise ValueError("Alpaca API not configured")
        
        try:
            self.client.cancel_order_by_id(order_id)
            return {"message": f"Order {order_id} cancelled successfully"}
        except Exception as e:
            raise Exception(f"Failed to cancel order: {str(e)}")
    
    async def close_position(self, symbol: str) -> Dict[str, Any]:
        """Close a position"""
        if not ALPACA_AVAILABLE:
            raise ValueError("Alpaca library not installed. Install it with: pip install alpaca-py")
        if not self.is_configured():
            raise ValueError("Alpaca API not configured")
        
        try:
            self.client.close_position(symbol)
            return {"message": f"Position {symbol} closed successfully"}
        except Exception as e:
            raise Exception(f"Failed to close position: {str(e)}")
    
    async def place_order(self, symbol: str, qty: float, side: str, order_type: str = "market", 
                         time_in_force: str = "day", limit_price: Optional[float] = None, 
                         stop_price: Optional[float] = None) -> Dict[str, Any]:
        """Place an order (generic method that handles different order types)"""
        if not ALPACA_AVAILABLE:
            raise ValueError("Alpaca library not installed. Install it with: pip install alpaca-py")
        if not self.is_configured():
            raise ValueError("Alpaca API not configured")
        
        try:
            if order_type == "market":
                return await self.place_market_order(symbol, qty, side)
            elif order_type == "limit":
                if limit_price is None:
                    raise ValueError("Limit price required for limit order")
                return await self.place_limit_order(symbol, qty, side, limit_price)
            else:
                raise ValueError(f"Unsupported order type: {order_type}")
        except Exception as e:
            raise Exception(f"Failed to place order: {str(e)}")
    
    async def cancel_all_orders(self) -> Dict[str, Any]:
        """Cancel all orders"""
        if not ALPACA_AVAILABLE:
            raise ValueError("Alpaca library not installed. Install it with: pip install alpaca-py")
        if not self.is_configured():
            raise ValueError("Alpaca API not configured")
        
        try:
            self.client.cancel_orders()
            return {"message": "All orders cancelled successfully"}
        except Exception as e:
            raise Exception(f"Failed to cancel all orders: {str(e)}")
    
    async def get_portfolio_history(self, period: str = "1M", timeframe: str = "1Day") -> Dict[str, Any]:
        """Get portfolio history"""
        if not ALPACA_AVAILABLE:
            raise ValueError("Alpaca library not installed. Install it with: pip install alpaca-py")
        if not self.is_configured():
            raise ValueError("Alpaca API not configured")
        
        try:
            # For now, return a placeholder
            # In production, you'd use Alpaca's portfolio history API
            return {
                "timestamp": [],
                "equity": [],
                "profit_loss": [],
                "profit_loss_pct": []
            }
        except Exception as e:
            raise Exception(f"Failed to get portfolio history: {str(e)}")
    
    def get_corporate_actions(self, start_date: str, end_date: str, action_type: Optional[str] = None, 
                             ca_types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Get corporate actions (including earnings) from Alpaca API
        This uses Alpaca's REST API directly for corporate actions
        
        Args:
            start_date: Start date (YYYY-MM-DD format)
            end_date: End date (YYYY-MM-DD format)
            action_type: Optional filter for action type (e.g., 'dividend', 'split', 'merger')
            ca_types: Optional list of corporate action types to filter
        
        Returns:
            List of corporate actions including earnings
        """
        import requests
        from datetime import datetime
        
        if not self.api_key or not self.api_secret:
            raise ValueError("Alpaca API keys not configured")
        
        try:
            # Alpaca Corporate Actions API endpoint
            url = f"{self.base_url}/v2/corporate_actions"
            
            headers = {
                'APCA-API-KEY-ID': self.api_key,
                'APCA-API-SECRET-KEY': self.api_secret
            }
            
            params = {
                'start': start_date,
                'end': end_date,
            }
            
            if action_type:
                params['action_type'] = action_type
            
            if ca_types:
                params['ca_types'] = ','.join(ca_types)
            
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            corporate_actions = data.get('corporate_actions', [])
            
            return corporate_actions
            
        except Exception as e:
            raise Exception(f"Failed to get corporate actions: {str(e)}")
    
    def get_corporate_actions_with_keys(self, api_key: str, api_secret: str, start_date: str, 
                                       end_date: str, base_url: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get corporate actions using provided API keys (for bot-specific requests)
        """
        import requests
        
        if not api_key or not api_secret:
            return []
        
        try:
            base = base_url or 'https://paper-api.alpaca.markets'
            url = f"{base}/v2/corporate_actions"
            
            headers = {
                'APCA-API-KEY-ID': api_key,
                'APCA-API-SECRET-KEY': api_secret
            }
            
            params = {
                'start': start_date,
                'end': end_date,
                'ca_types': 'dividend,split,merger,spinoff,earnings'  # Include earnings
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            corporate_actions = data.get('corporate_actions', [])
            
            return corporate_actions
            
            
        except Exception as e:
            print(f"[ALPACA] Error getting corporate actions: {e}")
            return []

    async def search_assets(self, query: str, api_key: Optional[str] = None, api_secret: Optional[str] = None, paper: bool = True) -> List[Dict[str, Any]]:
        """
        Search for assets (autocomplete)
        This caches the asset list to avoid hitting API rate limits
        """
        client_to_use = self.client
        
        # If not configured globally, try to use provided keys
        if not client_to_use:
            if api_key and api_secret and ALPACA_AVAILABLE:
                try:
                    from alpaca.trading.client import TradingClient
                    base_url = os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets') if paper else 'https://api.alpaca.markets'
                    client_to_use = TradingClient(
                        api_key=api_key,
                        secret_key=api_secret,
                        paper=paper,
                        url_override=base_url
                    )
                except Exception as e:
                    print(f"[ALPACA] Failed to create temp client: {e}")
                    return []
            else:
                # Fallback to local mapper if no generic client and no specific keys
                return symbol_mapper.search(query)
            
        try:
            # Simple caching strategy: if not cached or older than 24h, refresh
            # Note: We only cache if using the global client to avoid mixing user data or re-auth issues
            # Actually, for asset list it is public data so we can share cache or just re-fetch for temp client
            
            if client_to_use == self.client and (not hasattr(self, '_cached_assets') or not hasattr(self, '_assets_timestamp') or \
               (datetime.now() - self._assets_timestamp) > timedelta(hours=24)):
                
                print("[ALPACA] Refreshing asset cache...")
                # Fetch all active assets
                assets = client_to_use.get_all_assets(GetAssetsRequest(status=AssetStatus.ACTIVE, asset_class=AssetClass.US_EQUITY))
                self._cached_assets = [
                    {
                        "symbol": a.symbol,
                        "name": getattr(a, 'name', a.symbol),
                        "exchange": getattr(a, 'exchange', ''),
                        "tradable": getattr(a, 'tradable', True)
                    }
                    for a in assets if getattr(a, 'tradable', True)
                ]
                self._assets_timestamp = datetime.now()
                print(f"[ALPACA] Cached {len(self._cached_assets)} assets")
            
            # Perform local search
            q = query.strip().upper()
            if not q:
                return []
                
            # Filter matches: symbol starts with Q or name contains Q (case insensitive)
            matches = []
            for asset in self._cached_assets:
                if asset['symbol'].startswith(q) or q in asset['name'].upper():
                    matches.append(asset)
                    if len(matches) >= 20:  # Limit results
                        break
            
            # If no matches found in Alpaca cache, try symbol mapper
            if not matches:
                return symbol_mapper.search(query)
                
            return matches
            
        except Exception as e:
            print(f"[ALPACA] Error searching assets: {e}")
            # Fallback to local mapper on error
            return symbol_mapper.search(query)

# Create singleton instance
alpaca_service = AlpacaService()
