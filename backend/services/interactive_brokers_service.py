"""
Interactive Brokers Trading Service
Handles integration with Interactive Brokers TWS/Gateway API using ib_insync
"""
import os
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

# Try to import ib_insync library
try:
    from ib_insync import IB, Stock, Order, MarketOrder, LimitOrder, Trade, Contract, util
    IB_AVAILABLE = True
except ImportError:
    IB_AVAILABLE = False
    # Silently fail - IB is optional
    pass

from services.symbol_mapper import symbol_mapper


class InteractiveBrokersService:
    """
    Interactive Brokers Trading Service
    
    Connects to TWS (Trader Workstation) or IB Gateway for trading.
    
    Default Ports:
    - TWS Paper Trading: 7497
    - TWS Live Trading: 7496
    - IB Gateway Paper Trading: 4002
    - IB Gateway Live Trading: 4001
    """
    
    def __init__(
        self, 
        host: Optional[str] = None, 
        port: Optional[int] = None, 
        client_id: Optional[int] = None,
        account: Optional[str] = None,
        paper: bool = True,
        readonly: bool = False
    ):
        global IB_AVAILABLE
        
        # Get connection parameters from arguments or environment variables
        self.host = host or os.getenv('IB_HOST', '127.0.0.1')
        
        # Determine default port based on paper trading mode
        default_port = 7497 if paper else 7496  # TWS ports
        self.port = port or int(os.getenv('IB_PORT', str(default_port)))
        
        self.client_id = client_id or int(os.getenv('IB_CLIENT_ID', '1'))
        self.account = account or os.getenv('IB_ACCOUNT', '')
        self.paper = paper
        self.readonly = readonly
        
        self.ib = None
        self.init_error = None
        self._connected = False
        
        # If global import failed, try again here to capture the error
        if not IB_AVAILABLE:
            try:
                from ib_insync import IB
                IB_AVAILABLE = True
            except ImportError as e:
                self.init_error = f"Library Import Error: {str(e)}. Install with: pip install ib_insync"
                print(f"[IB] Import error: {e}")
                return
            except Exception as e:
                self.init_error = f"Library Init Error: {str(e)}"
                print(f"[IB] Init error: {e}")
                return
        
        # Create IB instance (don't connect yet - will connect on demand)
        try:
            from ib_insync import IB
            self.ib = IB()
        except Exception as e:
            print(f"Error creating IB instance: {e}")
            self.init_error = str(e)
    
    async def _ensure_connected(self) -> bool:
        """Ensure connection to TWS/Gateway, connecting if necessary"""
        if not IB_AVAILABLE:
            raise ValueError("ib_insync library not installed. Install it with: pip install ib_insync")
        
        if not self.ib:
            raise ValueError("IB instance not initialized")
        
        if self.ib.isConnected():
            return True
        
        try:
            # Connect to TWS/Gateway
            print(f"[IB] Connecting to {self.host}:{self.port} with client_id={self.client_id}...")
            await self.ib.connectAsync(
                host=self.host,
                port=self.port,
                clientId=self.client_id,
                readonly=self.readonly,
                timeout=20
            )
            
            self._connected = True
            print(f"[IB] Connected successfully")
            
            # If account specified, make sure it exists
            if self.account:
                accounts = self.ib.managedAccounts()
                if self.account not in accounts:
                    print(f"[IB] Warning: Account {self.account} not found. Available: {accounts}")
            
            return True
        except Exception as e:
            self.init_error = f"Connection failed: {str(e)}"
            print(f"[IB] Connection error: {e}")
            raise ValueError(f"Failed to connect to Interactive Brokers: {str(e)}")
    
    def is_configured(self) -> bool:
        """Check if IB is configured (has connection parameters)"""
        if not IB_AVAILABLE:
            return False
        return self.ib is not None and self.init_error is None
    
    async def get_account(self) -> Dict[str, Any]:
        """Get account information"""
        if not IB_AVAILABLE:
            raise ValueError("ib_insync library not installed. Install it with: pip install ib_insync")
        
        await self._ensure_connected()
        
        try:
            # Get account summary
            account_id = self.account or self.ib.managedAccounts()[0]
            account_values = self.ib.accountValues(account_id)
            
            # Parse account values into a dict
            account_data = {}
            for av in account_values:
                if av.currency == 'USD' or av.currency == '':
                    account_data[av.tag] = av.value
            
            # Get key metrics
            cash = float(account_data.get('TotalCashValue', 0))
            portfolio_value = float(account_data.get('NetLiquidation', 0))
            buying_power = float(account_data.get('BuyingPower', 0))
            equity = float(account_data.get('EquityWithLoanValue', 0))
            
            return {
                "account_number": account_id,
                "status": "ACTIVE" if self.ib.isConnected() else "DISCONNECTED",
                "currency": "USD",
                "buying_power": buying_power,
                "cash": cash,
                "portfolio_value": portfolio_value,
                "pattern_day_trader": account_data.get('DayTradesRemaining', '0') != 'unlimited',
                "trading_blocked": False,
                "transfers_blocked": False,
                "account_blocked": False,
                "created_at": None,
                "trade_suspended_by_user": False,
                "multiplier": 1.0,
                "equity": equity,
                "paper": self.paper,
                # IB specific
                "maintenance_margin": float(account_data.get('MaintMarginReq', 0)),
                "initial_margin": float(account_data.get('InitMarginReq', 0)),
                "available_funds": float(account_data.get('AvailableFunds', 0)),
            }
        except Exception as e:
            raise Exception(f"Failed to get account: {str(e)}")
    
    async def get_positions(self) -> List[Dict[str, Any]]:
        """Get all open positions"""
        if not IB_AVAILABLE:
            raise ValueError("ib_insync library not installed. Install it with: pip install ib_insync")
        
        await self._ensure_connected()
        
        try:
            positions = self.ib.positions()
            
            result = []
            for pos in positions:
                # Filter by account if specified
                if self.account and pos.account != self.account:
                    continue
                
                contract = pos.contract
                
                # Calculate unrealized P&L (requires market data)
                # For now, we'll provide basic info
                result.append({
                    "symbol": contract.symbol,
                    "qty": float(pos.position),
                    "side": "long" if pos.position > 0 else "short",
                    "market_value": float(pos.position) * float(pos.avgCost),  # Approximate
                    "cost_basis": float(pos.avgCost) * abs(float(pos.position)),
                    "unrealized_pl": 0.0,  # Would need market data subscription
                    "unrealized_plpc": 0.0,
                    "current_price": float(pos.avgCost),  # Using avg cost as placeholder
                    "lastday_price": 0.0,
                    "change_today": 0.0,
                    "avg_cost": float(pos.avgCost),
                    "contract_id": contract.conId,
                    "exchange": contract.exchange or contract.primaryExchange,
                    "security_type": contract.secType,
                })
            
            return result
        except Exception as e:
            raise Exception(f"Failed to get positions: {str(e)}")
    
    async def get_orders(self, status: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get orders (optionally filtered by status: open, closed, all)"""
        if not IB_AVAILABLE:
            raise ValueError("ib_insync library not installed. Install it with: pip install ib_insync")
        
        await self._ensure_connected()
        
        try:
            # Get all open orders
            open_orders = self.ib.openOrders()
            trades = self.ib.trades()
            
            result = []
            
            for trade in trades[:limit]:
                order = trade.order
                contract = trade.contract
                order_status = trade.orderStatus
                
                # Filter by status if specified
                if status == 'open' and order_status.status not in ['PreSubmitted', 'Submitted', 'PendingSubmit']:
                    continue
                elif status == 'closed' and order_status.status not in ['Filled', 'Cancelled', 'Inactive']:
                    continue
                
                result.append({
                    "id": str(order.orderId),
                    "symbol": contract.symbol,
                    "qty": float(order.totalQuantity),
                    "side": order.action.lower(),
                    "type": order.orderType,
                    "time_in_force": order.tif,
                    "status": order_status.status,
                    "filled_qty": float(order_status.filled),
                    "filled_avg_price": float(order_status.avgFillPrice) if order_status.avgFillPrice else None,
                    "limit_price": float(order.lmtPrice) if order.lmtPrice else None,
                    "stop_price": float(order.auxPrice) if order.auxPrice else None,
                    "submitted_at": None,  # IB doesn't provide this directly
                    "filled_at": None,
                    "remaining": float(order_status.remaining),
                    "perm_id": order.permId,
                })
            
            return result
        except Exception as e:
            raise Exception(f"Failed to get orders: {str(e)}")
    
    def _create_stock_contract(self, symbol: str) -> 'Contract':
        """Create a stock contract for the given symbol"""
        from ib_insync import Stock
        
        # Handle crypto symbols
        if '-' in symbol and symbol.endswith('USD'):
            from ib_insync import Crypto
            base_currency = symbol.replace('-USD', '')
            return Crypto(base_currency, 'PAXOS', 'USD')
        
        # Default to US stock
        return Stock(symbol, 'SMART', 'USD')
    
    async def place_market_order(self, symbol: str, qty: float, side: str) -> Dict[str, Any]:
        """Place a market order"""
        if not IB_AVAILABLE:
            raise ValueError("ib_insync library not installed. Install it with: pip install ib_insync")
        
        await self._ensure_connected()
        
        try:
            # Create contract
            contract = self._create_stock_contract(symbol)
            
            # Qualify the contract
            await self.ib.qualifyContractsAsync(contract)
            
            # Create market order
            action = 'BUY' if side.lower() == 'buy' else 'SELL'
            order = MarketOrder(action, qty)
            
            # Set account if specified
            if self.account:
                order.account = self.account
            
            # Place order
            trade = self.ib.placeOrder(contract, order)
            
            # Wait a moment for order to be submitted
            await asyncio.sleep(0.5)
            
            return {
                "id": str(trade.order.orderId),
                "symbol": symbol,
                "qty": float(qty),
                "side": side.lower(),
                "type": "market",
                "status": trade.orderStatus.status,
                "perm_id": trade.order.permId,
            }
        except Exception as e:
            err = str(e).lower()
            if "not connected" in err or "connection" in err:
                raise Exception(
                    "Interactive Brokers: Non connesso a TWS/Gateway. "
                    "Assicurati che TWS o IB Gateway sia in esecuzione e le impostazioni API siano corrette."
                )
            raise Exception(f"Failed to place order: {str(e)}")
    
    async def place_limit_order(self, symbol: str, qty: float, side: str, limit_price: float) -> Dict[str, Any]:
        """Place a limit order"""
        if not IB_AVAILABLE:
            raise ValueError("ib_insync library not installed. Install it with: pip install ib_insync")
        
        await self._ensure_connected()
        
        try:
            # Create contract
            contract = self._create_stock_contract(symbol)
            
            # Qualify the contract
            await self.ib.qualifyContractsAsync(contract)
            
            # Create limit order
            action = 'BUY' if side.lower() == 'buy' else 'SELL'
            order = LimitOrder(action, qty, limit_price)
            
            # Set account if specified
            if self.account:
                order.account = self.account
            
            # Place order
            trade = self.ib.placeOrder(contract, order)
            
            # Wait a moment for order to be submitted
            await asyncio.sleep(0.5)
            
            return {
                "id": str(trade.order.orderId),
                "symbol": symbol,
                "qty": float(qty),
                "side": side.lower(),
                "type": "limit",
                "limit_price": limit_price,
                "status": trade.orderStatus.status,
                "perm_id": trade.order.permId,
            }
        except Exception as e:
            raise Exception(f"Failed to place limit order: {str(e)}")
    
    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel an order"""
        if not IB_AVAILABLE:
            raise ValueError("ib_insync library not installed. Install it with: pip install ib_insync")
        
        await self._ensure_connected()
        
        try:
            # Find the order
            order_id_int = int(order_id)
            trades = self.ib.trades()
            
            for trade in trades:
                if trade.order.orderId == order_id_int:
                    self.ib.cancelOrder(trade.order)
                    return {"message": f"Order {order_id} cancelled successfully"}
            
            raise ValueError(f"Order {order_id} not found")
        except Exception as e:
            raise Exception(f"Failed to cancel order: {str(e)}")
    
    async def close_position(self, symbol: str) -> Dict[str, Any]:
        """Close a position"""
        if not IB_AVAILABLE:
            raise ValueError("ib_insync library not installed. Install it with: pip install ib_insync")
        
        await self._ensure_connected()
        
        try:
            # Find position
            positions = self.ib.positions()
            
            for pos in positions:
                if pos.contract.symbol == symbol:
                    # Filter by account if specified
                    if self.account and pos.account != self.account:
                        continue
                    
                    qty = abs(float(pos.position))
                    side = 'sell' if pos.position > 0 else 'buy'
                    
                    return await self.place_market_order(symbol, qty, side)
            
            raise ValueError(f"Position for {symbol} not found")
        except Exception as e:
            raise Exception(f"Failed to close position: {str(e)}")
    
    async def place_order(
        self, 
        symbol: str, 
        qty: float, 
        side: str, 
        order_type: str = "market",
        time_in_force: str = "day", 
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """Place an order (generic method that handles different order types)"""
        if order_type == "market":
            return await self.place_market_order(symbol, qty, side)
        elif order_type == "limit":
            if limit_price is None:
                raise ValueError("Limit price required for limit order")
            return await self.place_limit_order(symbol, qty, side, limit_price)
        else:
            raise ValueError(f"Unsupported order type: {order_type}")
    
    async def cancel_all_orders(self) -> Dict[str, Any]:
        """Cancel all orders"""
        if not IB_AVAILABLE:
            raise ValueError("ib_insync library not installed. Install it with: pip install ib_insync")
        
        await self._ensure_connected()
        
        try:
            self.ib.reqGlobalCancel()
            return {"message": "All orders cancelled successfully"}
        except Exception as e:
            raise Exception(f"Failed to cancel all orders: {str(e)}")
    
    async def get_portfolio_history(self, period: str = "1M", timeframe: str = "1Day") -> Dict[str, Any]:
        """Get portfolio history (placeholder - IB doesn't have a simple API for this)"""
        # Note: IB doesn't provide portfolio history directly like Alpaca
        # You'd need to track this yourself or use IB's Account & Portfolio reports
        return {
            "timestamp": [],
            "equity": [],
            "profit_loss": [],
            "profit_loss_pct": []
        }
    
    async def search_assets(self, query: str) -> List[Dict[str, Any]]:
        """Search for assets (symbols)"""
        if not IB_AVAILABLE:
            # Fallback to symbol mapper
            return symbol_mapper.search(query)
        
        try:
            await self._ensure_connected()
            
            # Search for symbols using IB's symbol search
            from ib_insync import Stock
            
            # Create a generic stock contract for search
            contract = Stock(query.upper(), 'SMART', 'USD')
            
            # Try to qualify
            try:
                contracts = await self.ib.qualifyContractsAsync(contract)
                
                return [
                    {
                        "symbol": c.symbol,
                        "name": c.localSymbol or c.symbol,
                        "exchange": c.primaryExchange or c.exchange,
                        "tradable": True,
                        "con_id": c.conId,
                    }
                    for c in contracts if c.conId
                ]
            except:
                pass
            
            # Fallback to symbol mapper
            return symbol_mapper.search(query)
            
        except Exception as e:
            print(f"[IB] Error searching assets: {e}")
            return symbol_mapper.search(query)
    
    async def disconnect(self):
        """Disconnect from TWS/Gateway"""
        if self.ib and self.ib.isConnected():
            self.ib.disconnect()
            self._connected = False
            print("[IB] Disconnected")
    
    def __del__(self):
        """Cleanup on destruction"""
        try:
            if self.ib and self.ib.isConnected():
                self.ib.disconnect()
        except:
            pass


# Create singleton instance (not connected by default)
ib_service = InteractiveBrokersService()
