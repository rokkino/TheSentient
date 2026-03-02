import yfinance as yf
import json

tk = yf.Ticker("AAPL")
news = tk.news

for n in news:
    content = n.get('content', n)
    tickers = content.get('relatedTickers', [])
    if 'finance' in content and 'relatedTickers' in content['finance']:
        print("TICKERS IN FINANCE KEY:", content['finance']['relatedTickers'])
    elif 'relatedTickers' in content:
        print("TICKERS IN CONTENT:", content['relatedTickers'])
    else:
        print("NO TICKERS EXTRACTABLE for:", content.get('title'))
