# TheSentient - AI Trading Bot Platform

An intelligent trading platform that uses AI (Google Gemini) to analyze earnings reports and generate automated trading decisions.

## Features

- 🤖 **AI-Powered Analysis**: Uses Google Gemini to analyze earnings reports and market data
- 📊 **Automated Trading**: Executes trades on Alpaca (paper trading) based on AI decisions
- 📈 **Real-time Market Data**: Fetches earnings calendars, stock prices, and market trends
- 🎯 **Smart Order Management**: Creates paired entry/exit orders with confidence scoring
- 🔄 **Symbol Normalization**: Automatically maps alternative symbols (GOLD→GLD, BTC→BITO, etc.)
- ⏰ **Scheduled Execution**: Background scheduler executes orders at specified times
- 💬 **Interactive Dashboard**: Vue.js frontend with real-time order tracking

## Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.12+)
- **Database**: SQLAlchemy + SQLite/PostgreSQL
- **AI**: Google Gemini API
- **Trading**: Alpaca API, IG Markets API
- **Scheduling**: APScheduler
- **Data**: yfinance, pandas, numpy

### Frontend
- **Framework**: Vue 3 + Vite
- **State Management**: Pinia
- **Charts**: Lightweight Charts
- **HTTP Client**: Axios
- **UI**: Custom CSS with modern design

## Installation

### Prerequisites
- Python 3.12+
- Node.js 18+
- Alpaca Paper Trading Account
- Google Gemini API Key

### Backend Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd TheSentient
```

2. **Create virtual environment**
```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**

Create a `.env` file in the `backend` directory:

```env
# Database
DATABASE_URL=sqlite:///./thesentient.db

# JWT Secret (generate a random string)
SECRET_KEY=your-secret-key-here

# Alpaca API (Paper Trading)
ALPACA_API_KEY=your-alpaca-api-key
ALPACA_API_SECRET=your-alpaca-secret-key
ALPACA_BASE_URL=https://paper-api.alpaca.markets

# Google Gemini API
GOOGLE_GEMINI_API_KEY=your-gemini-api-key

# Optional: IG Markets
IG_API_KEY=your-ig-api-key
IG_USERNAME=your-ig-username
IG_PASSWORD=your-ig-password
IG_ACC_NUMBER=your-ig-account-number
```

5. **Run the backend**
```bash
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at `http://localhost:8000`

### Frontend Setup

1. **Navigate to frontend directory**
```bash
cd frontend
```

2. **Install dependencies**
```bash
npm install
```

3. **Run the development server**
```bash
npm run dev
```

Frontend will be available at `http://localhost:5173`

## Usage

### 1. Create an Account
- Navigate to `http://localhost:5173`
- Register a new account
- Configure your API keys in the profile settings

### 2. Configure a Bot
- Go to the Bots section
- Click "Configure" on the "Earnings Report Genius" bot
- Select your trading account (Alpaca or IG Markets)
- Save the configuration

### 3. Activate the Bot
- Click "Activate" on the configured bot
- The bot will automatically:
  - Fetch earnings calendars for the next 5 days
  - Analyze companies in defense/AI sectors
  - Generate BUY/SELL decisions with confidence scores
  - Create paired entry/exit orders

### 4. Monitor Orders
- Click "Check Orders" to view pending and executed orders
- Orders show:
  - Symbol (with normalization: NV→NVDA, GOLD→GLD, etc.)
  - Decision (BUY/SELL)
  - Execution time
  - Confidence score
  - Reasoning from AI

### 5. Manual Order Creation
- In "Check Orders" modal, click "+ Add order"
- Enter symbol (supports alternatives: nv, nvidia, gold, btc, etc.)
- Select BUY/SELL
- Set execution time (optional)
- Add reasoning (optional)
- Click "Create"

## Symbol Normalization

The platform automatically normalizes alternative symbol names:

| Input | Output | Description |
|-------|--------|-------------|
| NV, NVIDIA | NVDA | NVIDIA Corporation |
| GOLD, XAU | GLD | Gold ETF |
| SILVER, XAG | SLV | Silver ETF |
| OIL, CRUDE | USO | Oil ETF |
| BTC, BITCOIN | BITO | Bitcoin ETF |
| ETH, ETHEREUM | ETHE | Ethereum ETF |
| SPX, SP500 | SPY | S&P 500 ETF |
| NDX, NASDAQ | QQQ | Nasdaq-100 ETF |

## Architecture

### Order Generation Flow
```
1. Bot Activation
   ↓
2. Fetch Earnings Calendar (next 5 days)
   ↓
3. Filter by Sector (Defense/AI)
   ↓
4. Gemini Analysis (confidence scoring)
   ↓
5. Create Paired Orders
   - Entry: 21:59 before earnings
   - Exit: 09:35 after earnings
   ↓
6. Store in Database (PENDING status)
```

### Order Execution Flow
```
1. Scheduler runs every minute
   ↓
2. Find PENDING orders where execution_time <= now
   ↓
3. Normalize symbols (GOLD→GLD, etc.)
   ↓
4. Execute on Alpaca/IG Markets
   ↓
5. Update status to EXECUTED
   ↓
6. Log order ID in reasoning
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login
- `GET /api/auth/me` - Get current user

### Bots
- `GET /api/bot` - List all bots
- `POST /api/bot/{bot_id}/activate` - Activate bot
- `POST /api/bot/{bot_id}/deactivate` - Deactivate bot
- `PUT /api/bot/{bot_id}/config` - Update bot configuration

### Orders (Decisions)
- `GET /api/bot/decisions` - List orders
- `POST /api/bot/decisions` - Create manual order
- `PUT /api/bot/decisions/{decision_id}` - Update order
- `DELETE /api/bot/decisions/{decision_id}` - Delete order

### Market Data
- `GET /api/market/earnings` - Get earnings calendar
- `GET /api/market/data/{symbol}` - Get stock data

## Development

### Project Structure
```
TheSentient/
├── backend/
│   ├── main.py                 # FastAPI app
│   ├── models/                 # SQLAlchemy models
│   │   ├── user.py
│   │   └── bot.py
│   ├── services/               # Business logic
│   │   ├── bot_service.py
│   │   ├── gemini_service.py
│   │   ├── alpaca_service.py
│   │   ├── earnings_service.py
│   │   ├── scheduler_jobs.py
│   │   └── symbol_mapper.py    # Symbol normalization
│   ├── memory/                 # Cache & logs
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Dashboard.vue
│   │   │   ├── BotCard.vue
│   │   │   └── ...
│   │   ├── stores/
│   │   ├── router/
│   │   └── main.js
│   └── package.json
│
└── README.md
```

### Running Tests
```bash
# Backend tests
cd backend
python test_symbol_mapper.py
python test_order_execution.py

# Frontend tests
cd frontend
npm run test
```

## Deployment

See [.github/workflows/deploy.yml](.github/workflows/deploy.yml) for automated deployment configuration.

## License

MIT License

## Support

For issues and questions, please open an issue on GitHub.
