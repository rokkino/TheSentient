"""
Symbol Mapper Service - Normalizes alternative symbol names to official ticker symbols
Handles common alternative names like GOLD→GLD, XAU→GLD, etc.
"""
from typing import Optional, Dict
import re

class SymbolMapper:
    """Maps alternative symbol names to official ticker symbols"""
    
    # Common symbol mappings
    SYMBOL_MAP = {
        # Gold
        'GOLD': 'GLD',
        'XAU': 'GLD',
        'XAUUSD': 'GLD',
        'GOLD/USD': 'GLD',
        
        # Silver
        'SILVER': 'SLV',
        'XAG': 'SLV',
        'XAGUSD': 'SLV',
        'SILVER/USD': 'SLV',
        
        # Oil
        'OIL': 'USO',
        'CRUDE': 'USO',
        'CRUDEOIL': 'USO',
        'WTI': 'USO',
        
        # Bitcoin
        'BITCOIN': 'BITO',
        'BTC': 'BITO',
        'BTCUSD': 'BITO',
        'BTC/USD': 'BITO',
        
        # Ethereum
        'ETHEREUM': 'ETHE',
        'ETH': 'ETHE',
        'ETHUSD': 'ETHE',
        'ETH/USD': 'ETHE',
        
        # Natural Gas
        'NATGAS': 'UNG',
        'NG': 'UNG',
        'NATURALGAS': 'UNG',
        
        # S&P 500
        'SPX': 'SPY',
        'SP500': 'SPY',
        'S&P500': 'SPY',
        
        # Nasdaq
        'NDX': 'QQQ',
        'NASDAQ': 'QQQ',
        'NASDAQ100': 'QQQ',
        
        # Dow Jones
        'DJI': 'DIA',
        'DJIA': 'DIA',
        'DOW': 'DIA',
        'DOWJONES': 'DIA',
    }
    
    def __init__(self):
        self.cache: Dict[str, str] = {}
    
    def normalize_symbol(self, symbol: str) -> str:
        """
        Normalize a symbol to its official ticker.
        
        Args:
            symbol: The symbol to normalize (e.g., "GOLD", "XAU", "PLTR")
            
        Returns:
            The normalized symbol (e.g., "GLD", "GLD", "PLTR")
        """
        if not symbol:
            return symbol
        
        # Clean the symbol
        symbol = symbol.strip().upper()
        
        # Remove common suffixes/prefixes
        symbol = symbol.replace('.US', '').replace('.NYSE', '').replace('.NASDAQ', '')
        
        # Check cache first
        if symbol in self.cache:
            return self.cache[symbol]
        
        # Check direct mapping
        if symbol in self.SYMBOL_MAP:
            normalized = self.SYMBOL_MAP[symbol]
            self.cache[symbol] = normalized
            print(f"[SymbolMapper] Normalized {symbol} → {normalized}")
            return normalized
        
        # If no mapping found, assume it's already a valid ticker
        self.cache[symbol] = symbol
        return symbol
    
    def add_mapping(self, alternative: str, official: str):
        """
        Add a custom symbol mapping.
        
        Args:
            alternative: The alternative symbol name
            official: The official ticker symbol
        """
        alternative = alternative.strip().upper()
        official = official.strip().upper()
        self.SYMBOL_MAP[alternative] = official
        self.cache[alternative] = official
        print(f"[SymbolMapper] Added mapping: {alternative} → {official}")
    
    def get_all_mappings(self) -> Dict[str, str]:
        """Get all current symbol mappings"""
        return self.SYMBOL_MAP.copy()

# Singleton instance
symbol_mapper = SymbolMapper()
