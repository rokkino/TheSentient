"""
Ticker Database - Local database of popular tickers for fast search
"""
from typing import List, Dict, Any

# Popular tickers database with names for fast local search
POPULAR_TICKERS = {
    # Tech
    'AAPL': {'name': 'Apple Inc.', 'type': 'EQUITY', 'exchange': 'NASDAQ'},
    'MSFT': {'name': 'Microsoft Corporation', 'type': 'EQUITY', 'exchange': 'NASDAQ'},
    'GOOGL': {'name': 'Alphabet Inc.', 'type': 'EQUITY', 'exchange': 'NASDAQ'},
    'GOOG': {'name': 'Alphabet Inc.', 'type': 'EQUITY', 'exchange': 'NASDAQ'},
    'AMZN': {'name': 'Amazon.com Inc.', 'type': 'EQUITY', 'exchange': 'NASDAQ'},
    'META': {'name': 'Meta Platforms Inc.', 'type': 'EQUITY', 'exchange': 'NASDAQ'},
    'NVDA': {'name': 'NVIDIA Corporation', 'type': 'EQUITY', 'exchange': 'NASDAQ'},
    'TSLA': {'name': 'Tesla Inc.', 'type': 'EQUITY', 'exchange': 'NASDAQ'},
    'NFLX': {'name': 'Netflix Inc.', 'type': 'EQUITY', 'exchange': 'NASDAQ'},
    'AMD': {'name': 'Advanced Micro Devices', 'type': 'EQUITY', 'exchange': 'NASDAQ'},
    'INTC': {'name': 'Intel Corporation', 'type': 'EQUITY', 'exchange': 'NASDAQ'},
    'CRM': {'name': 'Salesforce Inc.', 'type': 'EQUITY', 'exchange': 'NYSE'},
    'ORCL': {'name': 'Oracle Corporation', 'type': 'EQUITY', 'exchange': 'NYSE'},
    'ADBE': {'name': 'Adobe Inc.', 'type': 'EQUITY', 'exchange': 'NASDAQ'},
    'CSCO': {'name': 'Cisco Systems Inc.', 'type': 'EQUITY', 'exchange': 'NASDAQ'},
    'IBM': {'name': 'International Business Machines', 'type': 'EQUITY', 'exchange': 'NYSE'},
    'QCOM': {'name': 'Qualcomm Incorporated', 'type': 'EQUITY', 'exchange': 'NASDAQ'},
    'TXN': {'name': 'Texas Instruments Incorporated', 'type': 'EQUITY', 'exchange': 'NASDAQ'},
    'AVGO': {'name': 'Broadcom Inc.', 'type': 'EQUITY', 'exchange': 'NASDAQ'},
    
    # Finance
    'JPM': {'name': 'JPMorgan Chase & Co.', 'type': 'EQUITY', 'exchange': 'NYSE'},
    'BAC': {'name': 'Bank of America Corp', 'type': 'EQUITY', 'exchange': 'NYSE'},
    'WFC': {'name': 'Wells Fargo & Company', 'type': 'EQUITY', 'exchange': 'NYSE'},
    'GS': {'name': 'Goldman Sachs Group Inc.', 'type': 'EQUITY', 'exchange': 'NYSE'},
    'C': {'name': 'Citigroup Inc.', 'type': 'EQUITY', 'exchange': 'NYSE'},
    'V': {'name': 'Visa Inc.', 'type': 'EQUITY', 'exchange': 'NYSE'},
    'MA': {'name': 'Mastercard Incorporated', 'type': 'EQUITY', 'exchange': 'NYSE'},
    'PYPL': {'name': 'PayPal Holdings Inc.', 'type': 'EQUITY', 'exchange': 'NASDAQ'},
    'AXP': {'name': 'American Express Company', 'type': 'EQUITY', 'exchange': 'NYSE'},
    
    # Consumer
    'WMT': {'name': 'Walmart Inc.', 'type': 'EQUITY', 'exchange': 'NYSE'},
    'COST': {'name': 'Costco Wholesale Corporation', 'type': 'EQUITY', 'exchange': 'NASDAQ'},
    'HD': {'name': 'Home Depot Inc.', 'type': 'EQUITY', 'exchange': 'NYSE'},
    'MCD': {'name': "McDonald's Corporation", 'type': 'EQUITY', 'exchange': 'NYSE'},
    'NKE': {'name': 'Nike Inc.', 'type': 'EQUITY', 'exchange': 'NYSE'},
    'SBUX': {'name': 'Starbucks Corporation', 'type': 'EQUITY', 'exchange': 'NASDAQ'},
    'TGT': {'name': 'Target Corporation', 'type': 'EQUITY', 'exchange': 'NYSE'},
    'LOW': {'name': "Lowe's Companies Inc.", 'type': 'EQUITY', 'exchange': 'NYSE'},
    'BKNG': {'name': 'Booking Holdings Inc.', 'type': 'EQUITY', 'exchange': 'NASDAQ'},
    
    # Healthcare
    'JNJ': {'name': 'Johnson & Johnson', 'type': 'EQUITY', 'exchange': 'NYSE'},
    'PFE': {'name': 'Pfizer Inc.', 'type': 'EQUITY', 'exchange': 'NYSE'},
    'UNH': {'name': 'UnitedHealth Group Inc.', 'type': 'EQUITY', 'exchange': 'NYSE'},
    'ABBV': {'name': 'AbbVie Inc.', 'type': 'EQUITY', 'exchange': 'NYSE'},
    'MRK': {'name': 'Merck & Co. Inc.', 'type': 'EQUITY', 'exchange': 'NYSE'},
    'ABT': {'name': 'Abbott Laboratories', 'type': 'EQUITY', 'exchange': 'NYSE'},
    'TMO': {'name': 'Thermo Fisher Scientific Inc.', 'type': 'EQUITY', 'exchange': 'NYSE'},
    'DHR': {'name': 'Danaher Corporation', 'type': 'EQUITY', 'exchange': 'NYSE'},
    
    # Consumer Goods
    'PG': {'name': 'Procter & Gamble Company', 'type': 'EQUITY', 'exchange': 'NYSE'},
    'KO': {'name': 'The Coca-Cola Company', 'type': 'EQUITY', 'exchange': 'NYSE'},
    'PEP': {'name': 'PepsiCo Inc.', 'type': 'EQUITY', 'exchange': 'NASDAQ'},
    
    # Communication
    'T': {'name': 'AT&T Inc.', 'type': 'EQUITY', 'exchange': 'NYSE'},
    'VZ': {'name': 'Verizon Communications Inc.', 'type': 'EQUITY', 'exchange': 'NYSE'},
    'DIS': {'name': 'The Walt Disney Company', 'type': 'EQUITY', 'exchange': 'NYSE'},
    
    # Energy
    'XOM': {'name': 'Exxon Mobil Corporation', 'type': 'EQUITY', 'exchange': 'NYSE'},
    'CVX': {'name': 'Chevron Corporation', 'type': 'EQUITY', 'exchange': 'NYSE'},
    
    # Industrials
    'BA': {'name': 'The Boeing Company', 'type': 'EQUITY', 'exchange': 'NYSE'},
    'CAT': {'name': 'Caterpillar Inc.', 'type': 'EQUITY', 'exchange': 'NYSE'},
    'GE': {'name': 'General Electric Company', 'type': 'EQUITY', 'exchange': 'NYSE'},
    
    # Indices & Futures
    '^GSPC': {'name': 'S&P 500', 'type': 'INDEX', 'exchange': 'INDEX'},
    '^DJI': {'name': 'Dow Jones Industrial Average', 'type': 'INDEX', 'exchange': 'INDEX'},
    '^IXIC': {'name': 'NASDAQ Composite', 'type': 'INDEX', 'exchange': 'INDEX'},
    
    # Cryptocurrencies
    'BTC-USD': {'name': 'Bitcoin USD', 'type': 'CRYPTOCURRENCY', 'exchange': 'CCC'},
    'ETH-USD': {'name': 'Ethereum USD', 'type': 'CRYPTOCURRENCY', 'exchange': 'CCC'},
    'SOL-USD': {'name': 'Solana USD', 'type': 'CRYPTOCURRENCY', 'exchange': 'CCC'},
    'BNB-USD': {'name': 'Binance Coin USD', 'type': 'CRYPTOCURRENCY', 'exchange': 'CCC'},
    'XRP-USD': {'name': 'XRP USD', 'type': 'CRYPTOCURRENCY', 'exchange': 'CCC'},
    'ADA-USD': {'name': 'Cardano USD', 'type': 'CRYPTOCURRENCY', 'exchange': 'CCC'},
    'DOGE-USD': {'name': 'Dogecoin USD', 'type': 'CRYPTOCURRENCY', 'exchange': 'CCC'},
    'AVAX-USD': {'name': 'Avalanche USD', 'type': 'CRYPTOCURRENCY', 'exchange': 'CCC'},

    # Futures
    'ES=F': {'name': 'S&P 500 Futures', 'type': 'FUTURE', 'exchange': 'CME'},
    'NQ=F': {'name': 'Nasdaq 100 Futures', 'type': 'FUTURE', 'exchange': 'CME'},
    'YM=F': {'name': 'Dow Jones Futures', 'type': 'FUTURE', 'exchange': 'CBOT'},
    'RTY=F': {'name': 'Russell 2000 Futures', 'type': 'FUTURE', 'exchange': 'CME'},
    'GC=F': {'name': 'Gold Futures', 'type': 'FUTURE', 'exchange': 'CME'},
    'CL=F': {'name': 'Crude Oil Futures', 'type': 'FUTURE', 'exchange': 'NYMEX'},
    'SI=F': {'name': 'Silver Futures', 'type': 'FUTURE', 'exchange': 'CME'},
    'NG=F': {'name': 'Natural Gas Futures', 'type': 'FUTURE', 'exchange': 'NYMEX'},
    'HG=F': {'name': 'Copper Futures', 'type': 'FUTURE', 'exchange': 'COMEX'},
    'ZB=F': {'name': 'U.S. Treasury Bond Futures', 'type': 'FUTURE', 'exchange': 'CBOT'},
    'ZN=F': {'name': '10-Year T-Note Futures', 'type': 'FUTURE', 'exchange': 'CBOT'},
}

def search_local(query: str) -> List[Dict[str, Any]]:
    """Fast local search in ticker database"""
    if not query:
        return []
    
    query_upper = query.strip().upper()
    query_lower = query.strip().lower()
    results = []
    
    # Exact ticker match (fastest)
    if query_upper in POPULAR_TICKERS:
        ticker_data = POPULAR_TICKERS[query_upper]
        results.append({
            "symbol": query_upper,
            "name": ticker_data['name'],
            "type": ticker_data['type'],
            "exchange": ticker_data['exchange']
        })
        return results
    
    # Search by name (case-insensitive partial match)
    for ticker, data in POPULAR_TICKERS.items():
        name_lower = data['name'].lower()
        if query_lower in name_lower or name_lower.startswith(query_lower):
            results.append({
                "symbol": ticker,
                "name": data['name'],
                "type": data['type'],
                "exchange": data['exchange']
            })
    
    # Also check if query is a partial ticker match
    if len(query_upper) >= 1:
        for ticker, data in POPULAR_TICKERS.items():
            if ticker.startswith(query_upper) and ticker not in [r['symbol'] for r in results]:
                results.append({
                    "symbol": ticker,
                    "name": data['name'],
                    "type": data['type'],
                    "exchange": data['exchange']
                })
    
    # Limit results to top 10
    return results[:10]

