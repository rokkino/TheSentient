"""
Watchlist Service - Manages user watchlist
"""
import json
import os
from typing import List, Dict, Any

WATCHLIST_FILE = "watchlist.json"

class WatchlistService:
    def __init__(self):
        self.watchlist_file = WATCHLIST_FILE
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
        watchlist = self.get_watchlist()
        
        # Check if already exists
        if any(item['symbol'] == symbol for item in watchlist):
            return
        
        watchlist.append({
            "symbol": symbol,
            "name": name
        })
        
        self._save_watchlist(watchlist)
    
    def remove_item(self, symbol: str):
        """Remove item from watchlist"""
        watchlist = self.get_watchlist()
        watchlist = [item for item in watchlist if item['symbol'] != symbol]
        self._save_watchlist(watchlist)
    
    def _save_watchlist(self, watchlist: List[Dict[str, Any]]):
        """Save watchlist to file"""
        with open(self.watchlist_file, 'w') as f:
            json.dump(watchlist, f, indent=2)

