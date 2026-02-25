"""
Market Data Service - Fetches additional market data for earnings analysis
"""
import yfinance as yf
from typing import Dict, Any, Optional
import requests
from bs4 import BeautifulSoup
import re

class MarketDataService:
    def __init__(self):
        self.cache = {}
    
    def get_stock_data(self, symbol: str) -> Dict[str, Any]:
        """
        Get comprehensive stock data including:
        - Current price
        - P/E ratio
        - Short interest
        - IV Rank (approximated)
        - Market cap
        - Beta
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Get current price
            current_price = info.get('currentPrice') or info.get('regularMarketPrice', 0)
            
            # Get P/E ratio
            pe_ratio = info.get('trailingPE') or info.get('forwardPE', 0)
            
            # Get short interest
            short_percent = info.get('shortPercentOfFloat', 0)
            if short_percent:
                short_percent = short_percent * 100  # Convert to percentage
            
            # Get implied volatility (from options if available)
            iv_rank = self._get_iv_rank(ticker, symbol)
            
            # Additional metrics
            market_cap = info.get('marketCap', 0)
            beta = info.get('beta', 1.0)
            
            # Get 2-week price change for run-up detection
            hist = ticker.history(period="1mo")
            if len(hist) >= 10:
                two_weeks_ago_price = hist['Close'].iloc[-10]
                current_close = hist['Close'].iloc[-1]
                two_week_change = ((current_close - two_weeks_ago_price) / two_weeks_ago_price) * 100
            else:
                two_week_change = 0
            
            return {
                'symbol': symbol,
                'current_price': round(current_price, 2),
                'pe_ratio': round(pe_ratio, 2) if pe_ratio else None,
                'short_interest': f"{round(short_percent, 2)}%" if short_percent else "N/A",
                'iv_rank': iv_rank,
                'market_cap': market_cap,
                'beta': round(beta, 2) if beta else None,
                'two_week_change_pct': round(two_week_change, 2),
                'run_up_warning': two_week_change > 10  # Flag if >10% run-up
            }
            
        except Exception as e:
            print(f"[MarketData] Error fetching data for {symbol}: {e}")
            return {
                'symbol': symbol,
                'current_price': 0,
                'pe_ratio': None,
                'short_interest': "N/A",
                'iv_rank': "N/A",
                'market_cap': 0,
                'beta': None,
                'two_week_change_pct': 0,
                'run_up_warning': False
            }
    
    def _get_iv_rank(self, ticker, symbol: str) -> str:
        """
        Get IV Rank (approximated from options data)
        IV Rank = (Current IV - 52-week Low IV) / (52-week High IV - 52-week Low IV) * 100
        """
        try:
            # Try to get options data
            options_dates = ticker.options
            if not options_dates:
                return "N/A"
            
            # Get nearest expiration
            nearest_exp = options_dates[0]
            opt_chain = ticker.option_chain(nearest_exp)
            
            # Calculate average IV from ATM options
            calls = opt_chain.calls
            if len(calls) > 0:
                # Get ATM options (closest to current price)
                current_price = ticker.info.get('currentPrice', 0)
                if current_price > 0:
                    calls['strike_diff'] = abs(calls['strike'] - current_price)
                    atm_calls = calls.nsmallest(3, 'strike_diff')
                    avg_iv = atm_calls['impliedVolatility'].mean()
                    
                    # Approximate IV Rank (simplified - would need historical data for true IV Rank)
                    # For now, just return the IV percentage
                    if avg_iv > 0:
                        iv_pct = avg_iv * 100
                        return f"{round(iv_pct, 1)}%"
            
            return "N/A"
            
        except Exception as e:
            print(f"[MarketData] Could not get IV for {symbol}: {e}")
            return "N/A"
    
    def get_analyst_revisions(self, symbol: str) -> Dict[str, Any]:
        """
        Get analyst estimate revisions (trend up or down)
        """
        try:
            ticker = yf.Ticker(symbol)
            
            # Get analyst recommendations
            recommendations = ticker.recommendations
            if recommendations is not None and len(recommendations) > 0:
                recent = recommendations.tail(10)
                
                # Count upgrades vs downgrades
                upgrades = len(recent[recent['To Grade'].str.contains('Buy|Outperform', case=False, na=False)])
                downgrades = len(recent[recent['To Grade'].str.contains('Sell|Underperform', case=False, na=False)])
                
                if upgrades > downgrades:
                    trend = "Bullish (more upgrades)"
                elif downgrades > upgrades:
                    trend = "Bearish (more downgrades)"
                else:
                    trend = "Neutral"
                
                return {
                    'trend': trend,
                    'upgrades': upgrades,
                    'downgrades': downgrades
                }
            
            return {'trend': 'N/A', 'upgrades': 0, 'downgrades': 0}
            
        except Exception as e:
            print(f"[MarketData] Could not get analyst revisions for {symbol}: {e}")
            return {'trend': 'N/A', 'upgrades': 0, 'downgrades': 0}

# Singleton instance
market_data_service = MarketDataService()
