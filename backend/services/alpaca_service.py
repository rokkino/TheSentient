"""
Alpaca Paper Trading Service
Handles integration with Alpaca Markets API for paper trading
"""
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

# Try to import Alpaca libraries - make it optional
try:
    from alpaca.trade.client import TradeClient
    from alpaca.trade.requests import MarketOrderRequest, LimitOrderRequest, StopOrderRequest
    from alpaca.trade.enums import OrderSide, TimeInForce
    from alpaca.data.historical import StockHistoricalDataClient
    from alpaca.data.requests import StockBarsRequest
    from alpaca.data.timeframe import TimeFrame
    ALPACA_AVAILABLE = True
except ImportError:
    ALPACA_AVAILABLE = False
    # Silently fail - Alpaca is optional, we use IG Markets now
    pass

class AlpacaService:
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None, paper: bool = True):
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
        
        if not ALPACA_AVAILABLE:
            # Silently handle missing Alpaca - it's optional
            return
        
        if self.api_key and self.api_secret:
            try:
                self.client = TradeClient(
                    api_key=self.api_key,
                    secret_key=self.api_secret,
                    base_url=self.base_url,
                    api_version='v2'
                )
                self.data_client = StockHistoricalDataClient(
                    api_key=self.api_key,
                    secret_key=self.api_secret
                )
            except Exception as e:
                print(f"Error initializing Alpaca client: {e}")
                pass
    
    def is_configured(self) -> bool:
        """Check if Alpaca API is configured"""
        if not ALPACA_AVAILABLE:
            return False
        return self.client is not None and self.data_client is not None
    
    async def get_account(self) -> Dict[str, Any]:
        """Get account information"""
        if not ALPACA_AVAILABLE:
            raise ValueError("Alpaca library not installed. Install it with: pip install alpaca-trade-api")
        if not self.is_configured():
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
                "created_at": account.created_at.isoformat() if account.created_at else None,
                "trade_suspended_by_user": account.trade_suspended_by_user,
                "multiplier": float(account.multiplier) if hasattr(account, 'multiplier') else 1.0,
                "equity": float(account.equity) if hasattr(account, 'equity') else float(account.portfolio_value),
            }
        except Exception as e:
            raise Exception(f"Failed to get account: {str(e)}")
    
    async def get_positions(self) -> List[Dict[str, Any]]:
        """Get all open positions"""
        if not ALPACA_AVAILABLE:
            raise ValueError("Alpaca library not installed. Install it with: pip install alpaca-trade-api")
        if not self.is_configured():
            raise ValueError("Alpaca API not configured")
        
        try:
            positions = self.client.get_all_positions()
            return [
                {
                    "symbol": pos.symbol,
                    "qty": float(pos.qty),
                    "side": pos.side,
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
            raise ValueError("Alpaca library not installed. Install it with: pip install alpaca-trade-api")
        if not self.is_configured():
            raise ValueError("Alpaca API not configured")
        
        try:
            if status:
                orders = self.client.get_orders(status=status, limit=limit)
            else:
                orders = self.client.get_orders(limit=limit)
            
            return [
                {
                    "id": order.id,
                    "symbol": order.symbol,
                    "qty": float(order.qty),
                    "side": order.side,
                    "type": order.order_type,
                    "time_in_force": order.time_in_force,
                    "status": order.status,
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
    
    async def place_market_order(self, symbol: str, qty: float, side: str) -> Dict[str, Any]:
        """Place a market order"""
        if not ALPACA_AVAILABLE:
            raise ValueError("Alpaca library not installed. Install it with: pip install alpaca-trade-api")
        if not self.is_configured():
            raise ValueError("Alpaca API not configured")
        
        try:
            order_data = MarketOrderRequest(
                symbol=symbol,
                qty=qty,
                side=OrderSide.BUY if side.lower() == 'buy' else OrderSide.SELL,
                time_in_force=TimeInForce.DAY
            )
            order = self.client.submit_order(order_data=order_data)
            return {
                "id": order.id,
                "symbol": order.symbol,
                "qty": float(order.qty),
                "side": order.side,
                "type": order.order_type,
                "status": order.status,
            }
        except Exception as e:
            raise Exception(f"Failed to place order: {str(e)}")
    
    async def place_limit_order(self, symbol: str, qty: float, side: str, limit_price: float) -> Dict[str, Any]:
        """Place a limit order"""
        if not ALPACA_AVAILABLE:
            raise ValueError("Alpaca library not installed. Install it with: pip install alpaca-trade-api")
        if not self.is_configured():
            raise ValueError("Alpaca API not configured")
        
        try:
            order_data = LimitOrderRequest(
                symbol=symbol,
                qty=qty,
                side=OrderSide.BUY if side.lower() == 'buy' else OrderSide.SELL,
                limit_price=limit_price,
                time_in_force=TimeInForce.DAY
            )
            order = self.client.submit_order(order_data=order_data)
            return {
                "id": order.id,
                "symbol": order.symbol,
                "qty": float(order.qty),
                "side": order.side,
                "type": order.order_type,
                "limit_price": float(order.limit_price) if order.limit_price else None,
                "status": order.status,
            }
        except Exception as e:
            raise Exception(f"Failed to place limit order: {str(e)}")
    
    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel an order"""
        if not ALPACA_AVAILABLE:
            raise ValueError("Alpaca library not installed. Install it with: pip install alpaca-trade-api")
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
            raise ValueError("Alpaca library not installed. Install it with: pip install alpaca-trade-api")
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
            raise ValueError("Alpaca library not installed. Install it with: pip install alpaca-trade-api")
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
            raise ValueError("Alpaca library not installed. Install it with: pip install alpaca-trade-api")
        if not self.is_configured():
            raise ValueError("Alpaca API not configured")
        
        try:
            self.client.cancel_all_orders()
            return {"message": "All orders cancelled successfully"}
        except Exception as e:
            raise Exception(f"Failed to cancel all orders: {str(e)}")
    
    async def get_portfolio_history(self, period: str = "1M", timeframe: str = "1Day") -> Dict[str, Any]:
        """Get portfolio history"""
        if not ALPACA_AVAILABLE:
            raise ValueError("Alpaca library not installed. Install it with: pip install alpaca-trade-api")
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

# Create singleton instance
alpaca_service = AlpacaService()
