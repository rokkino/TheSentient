"""
Watchlist Service - Manages user watchlist
"""
import json
import os
from typing import List, Dict, Any

WATCHLIST_FILE = "watchlist.json"

class WatchlistService:
    def __init__(self):
        # Use absolute path relative to this file's directory
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.watchlist_file = os.path.join(base_dir, WATCHLIST_FILE)
        print(f"WatchlistService initialized with file: {self.watchlist_file}")
        self._ensure_file()
    
    def _ensure_file(self):
        """Ensure watchlist file exists"""
        if not os.path.exists(self.watchlist_file):
            with open(self.watchlist_file, 'w') as f:
                json.dump([], f)
    
    def get_watchlist(self) -> List[Dict[str, Any]]:
        """Get current watchlist"""
        try:
            with open(self.watchlist_file, 'r') as f:
                return json.load(f)
        except:
            return []
    
    def add_item(self, symbol: str, name: str):
        """Add item to watchlist"""
        print(f"Service: Adding item {symbol}")
        watchlist = self.get_watchlist()
        
        # Check if already exists
        if any(item['symbol'] == symbol for item in watchlist):
            print(f"Service: Item {symbol} already exists")
            return
        
        watchlist.append({
            "symbol": symbol,
            "name": name
        })
        
        self._save_watchlist(watchlist)
        print(f"Service: Watchlist saved with {len(watchlist)} items")
    
    def remove_item(self, symbol: str):
        """Remove item from watchlist"""
        watchlist = self.get_watchlist()
        watchlist = [item for item in watchlist if item['symbol'] != symbol]
        self._save_watchlist(watchlist)
    
    def _save_watchlist(self, watchlist: List[Dict[str, Any]]):
        """Save watchlist to file"""
        with open(self.watchlist_file, 'w') as f:
            json.dump(watchlist, f, indent=2)

