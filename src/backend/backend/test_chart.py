import sys
import os
import asyncio
BACKEND_DIR = r'C:\Users\gianluca.rocca\OneDrive - alpitronic GmbH\Documents\vscode\TheSentient\src\backend\backend'
sys.path.insert(0, BACKEND_DIR)
from services.market_data import MarketDataService

async def main():
    try:
        service = MarketDataService()
        data = await service.get_chart_data(ticker='AAPL', timeframe='1m', chart_type='candle', include_earnings=True)
        print('Chart OK:', len(data['data']), 'candles')
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(main())
