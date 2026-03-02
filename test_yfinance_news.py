import yfinance as yf
import json

tk = yf.Ticker("AAPL")
news = tk.news

if news:
    print(json.dumps(news[0], indent=2))
else:
    print("No news found")
