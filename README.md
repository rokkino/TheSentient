# The Sentient - Portfolio Tracker & News Analyzer

A modern, web-based portfolio tracking application with real-time news feeds and AI-powered trading signal analysis.

## Architecture

- **Frontend**: Vue.js 3 with Vite (hot reload enabled)
- **Backend**: FastAPI (Python) with WebSocket support
- **Charts**: TradingView Lightweight Charts
- **Real-time**: WebSocket for live news updates

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- npm or yarn

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Create virtual environment (recommended):
```bash
python -m venv venv
```

3. Activate virtual environment:
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

5. Start the backend server:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server (with hot reload):
```bash
npm run dev
```

The frontend will be available at `http://localhost:5173`

## Development

### Hot Reload

Both frontend and backend support hot reload:

- **Frontend**: Vite automatically reloads on file changes
- **Backend**: Uvicorn reloads on Python file changes (enabled by default)

### Project Structure

```
TheSentient/
├── backend/
│   ├── main.py                 # FastAPI application
│   ├── services/               # Business logic services
│   │   ├── market_data.py     # Chart data service
│   │   ├── news_service.py    # News fetching service
│   │   ├── watchlist_service.py
│   │   ├── search_service.py
│   │   └── ai_service.py      # AI analysis service
│   ├── websocket_manager.py   # WebSocket connection manager
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/        # Vue components
│   │   ├── views/             # Page views
│   │   ├── stores/            # Pinia stores
│   │   ├── services/          # API services
│   │   └── router/            # Vue Router
│   ├── package.json
│   └── vite.config.js
└── README.md
```

## Features

- 📊 **Interactive Charts** - Real-time candlestick and line charts
- 📰 **Live News Feed** - WebSocket-powered real-time news updates
- 🤖 **AI Analysis** - Automated trading signal generation
- 👀 **Watchlist** - Manage your favorite assets
- 🔄 **Hot Reload** - Instant updates during development
- 🎨 **Modern UI** - Dark theme with smooth animations

## API Endpoints

### Market Data
- `POST /api/chart` - Get chart data
- `GET /api/quote/{ticker}` - Get current quote

### Search
- `POST /api/search` - Search for assets

### Watchlist
- `GET /api/watchlist` - Get watchlist
- `POST /api/watchlist` - Add to watchlist
- `DELETE /api/watchlist/{symbol}` - Remove from watchlist

### News
- `GET /api/news` - Get news feed
- `GET /api/news/{ticker}` - Get ticker-specific news

### AI
- `POST /api/analyze` - Analyze news with AI

### WebSocket
- `WS /ws` - Real-time updates

## Production Build

### Frontend
```bash
cd frontend
npm run build
```

The built files will be in `frontend/dist/`

### Backend
The backend can be run with any ASGI server:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Troubleshooting

### Backend won't start
- Check Python version (3.11+)
- Verify all dependencies are installed
- Check if port 8000 is available

### Frontend won't start
- Check Node.js version (18+)
- Delete `node_modules` and run `npm install` again
- Check if port 5173 is available

### WebSocket connection fails
- Ensure backend is running
- Check CORS settings in `backend/main.py`
- Verify proxy settings in `frontend/vite.config.js`

## License & Disclaimer

**DISCLAIMER**: This software is for educational purposes only. Trading involves risk of loss. Always do your own research.

---

**Enjoy using The Sentient!** 📊📰🤖
