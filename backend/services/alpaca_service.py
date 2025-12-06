"""
Alpaca Paper Trading Service
Handles integration with Alpaca Markets API for paper trading
"""
import os
from typing import Dict, Any, List, Optional
from alpaca.trade.client import TradeClient
from alpaca.trade.requests import MarketOrderRequest, LimitOrderRequest, StopOrderRequest
from alpaca.trade.enums import OrderSide, TimeInForce
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from datetime import datetime, timedelta

class AlpacaService:
    def __init__(self):
        # Get API keys from environment variables
        self.api_key = os.getenv('ALPACA_API_KEY', '')
        self.api_secret = os.getenv('ALPACA_API_SECRET', '')
        self.base_url = os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets')  # Paper trading URL
        
        self.client = None
        self.data_client = None
        
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
                print(f"Warning: Failed to initialize Alpaca client: {e}")
    
    def is_configured(self) -> bool:
        """Check if Alpaca API is configured"""
        return self.client is not None and self.data_client is not None
    
    async def get_account(self) -> Dict[str, Any]:
        """Get account information"""
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
        if not self.is_configured():
            raise ValueError("Alpaca API not configured")
        
        try:
            self.client.cancel_order_by_id(order_id)
            return {"message": f"Order {order_id} cancelled successfully"}
        except Exception as e:
            raise Exception(f"Failed to cancel order: {str(e)}")
    
    async def close_position(self, symbol: str) -> Dict[str, Any]:
        """Close a position"""
        if not self.is_configured():
            raise ValueError("Alpaca API not configured")
        
        try:
            self.client.close_position(symbol)
            return {"message": f"Position {symbol} closed successfully"}
        except Exception as e:
            raise Exception(f"Failed to close position: {str(e)}")

# Create singleton instance
alpaca_service = AlpacaService()
