import json
import os
from pathlib import Path
import yfinance as yf

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
WATCHLIST_FILE = DATA_DIR / "watchlist.json"

class WatchlistService:
    @staticmethod
    def _ensure_file():
        if not WATCHLIST_FILE.exists():
            WATCHLIST_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(WATCHLIST_FILE, 'w') as f:
                json.dump([], f)

    @staticmethod
    def get_watchlist():
        WatchlistService._ensure_file()
        try:
            with open(WATCHLIST_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            return []

    @staticmethod
    def add_symbol(symbol: str):
        WatchlistService._ensure_file()
        symbol = symbol.upper().strip()
        
        # Validate with yfinance
        ticker = yf.Ticker(symbol)
        history = ticker.history(period="1d")
        if history.empty:
            return {"success": False, "message": f"Symbol {symbol} not found or invalid."}
            
        current_list = WatchlistService.get_watchlist()
        if symbol in current_list:
            return {"success": False, "message": f"Symbol {symbol} is already in the watchlist."}
            
        current_list.append(symbol)
        with open(WATCHLIST_FILE, 'w') as f:
            json.dump(current_list, f)
            
        return {"success": True, "message": f"Added {symbol} to watchlist.", "symbol": symbol}

    @staticmethod
    def remove_symbol(symbol: str):
        WatchlistService._ensure_file()
        symbol = symbol.upper().strip()
        
        current_list = WatchlistService.get_watchlist()
        if symbol not in current_list:
            return {"success": False, "message": f"Symbol {symbol} not found in watchlist."}
            
        current_list.remove(symbol)
        with open(WATCHLIST_FILE, 'w') as f:
            json.dump(current_list, f)
            
        return {"success": True, "message": f"Removed {symbol} from watchlist."}
