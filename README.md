# The Sentient - Portfolio Tracker & News Analyzer

A modern, feature-rich portfolio tracking application with real-time news feeds and AI-powered trading signal analysis.

## Features

- 📊 **Interactive Stock Charts** - Beautiful candlestick and line charts with multiple timeframes
- 📰 **Real-time News Feed** - Automatic news aggregation from Yahoo Finance
- 🤖 **AI Trading Signals** - Automated analysis of news with bullish/bearish indicators, confidence levels, stop loss, and take profit targets
- 📈 **RSI Indicator** - Built-in Relative Strength Index technical indicator
- 👀 **Watchlist Management** - Easy search and add stocks, ETFs, cryptocurrencies, and futures
- 🎨 **Modern UI** - Dark theme with rounded corners and smooth animations
- 🔄 **Multiple View Modes** - Three different viewing modes to suit your workflow

## Installation

### Prerequisites

- Python 3.10 or higher
- Internet connection (for fetching market data and news)

### Required Python Packages

Install the required packages using pip:

```bash
pip install PyQt6 pandas yfinance mplfinance matplotlib requests beautifulsoup4
```

### Optional Packages (for AI Analysis)

If you want AI-powered trading signal analysis, you'll also need:

```bash
pip install torch transformers
```

**Note:** PyTorch installation can be complex on Windows. If you encounter DLL errors, the application will still work without AI features.

### Required Files

Make sure you have these files in your project directory:

- `graph.py` - Main application file
- `news.py` - News fetching module
- `settings_view.py` - UI components
- `rsi.py` - RSI indicator (optional)
- `model.py` - AI analysis module (optional)
- `spinner.gif` - Loading animation

## Quick Start

1. **Run the application:**
   ```bash
   python graph.py
   ```

2. **Add assets to your watchlist:**
   - Type a ticker symbol or company name in the search bar
   - Select from the search results
   - Click the checkmark button or click on a search result

3. **View charts:**
   - Click on any asset in your watchlist to view its chart
   - Use timeframe buttons (1d, 5d, 1m, 3m, 6m, 1y, 5y) to change the time period
   - Toggle between Candle and Line chart types
   - Enable RSI indicator if available

## View Modes

The application has three view modes that you can cycle through using the view button (top-right toolbar):

### View Mode 1: Chart Only
- Full-screen chart view
- Perfect for focused technical analysis
- No distractions from news

### View Mode 2: Chart + Sidebar News
- Chart on the left, news feed on the right
- News updates in real-time
- Great for staying informed while trading

### View Mode 3: Chart + Flyout News
- Chart visible with a collapsible news panel on the right
- News panel appears when:
  - You move your mouse near the right edge of the screen
  - New news arrives
- Automatically hides after 5 seconds
- Only shows news related to your watchlist
- Perfect for minimal distractions while keeping an eye on news

## Using the News Feed

### View Mode 2 (Sidebar)
- News appears automatically in the right sidebar
- Click on any news card to open the full article in your browser
- News updates every 5 minutes

### View Mode 3 (Flyout)
- Move your mouse to the right edge of the screen to show the news panel
- The panel automatically slides in when new news arrives
- Hover over the panel to keep it visible
- Move away to hide it (auto-hides after 5 seconds)
- Click the "View" button in the panel header to change view modes

## AI Trading Signals

When AI analysis is enabled (requires `model.py` and PyTorch):

- **Automatic Analysis**: News items are automatically analyzed when they arrive
- **Trading Signals**: Each news card shows:
  - **Direction**: BULLISH (green) or BEARISH (red)
  - **Confidence**: Percentage (0-100%)
  - **Stop Loss**: Recommended stop loss percentage
  - **Take Profit**: Recommended take profit percentage

**Important Disclaimer**: AI-generated signals are for educational purposes only. Always do your own research and never rely solely on automated signals for trading decisions.

## Chart Features

### Timeframes
- **1d, 5d**: Intraday charts (2-minute and 15-minute intervals)
- **1m, 3m, 6m**: Daily charts
- **1y, 5y**: Daily and weekly charts

### Chart Types
- **Candle**: Traditional candlestick chart showing OHLC data
- **Line**: Simple line chart showing closing prices

### Indicators
- **RSI (Relative Strength Index)**: Shows momentum indicator in a separate panel below the chart
- Enable/disable with the RSI button in the toolbar

### Chart Interactions
- **Hover**: Move your mouse over the chart to see detailed price information
- **Zoom**: Charts automatically adjust based on visible data
- **Volume**: Volume bars are displayed below the price chart

## Watchlist Management

### Adding Assets
1. Type in the search bar (top of left panel)
2. Wait for search results to appear
3. Click on a result or use the checkmark button
4. The asset is added to your watchlist

### Removing Assets
1. Select an asset in your watchlist
2. Click the "Remove" button at the bottom of the watchlist
3. The asset is removed and settings are saved

### Supported Asset Types
- Stocks (e.g., AAPL, MSFT, TSLA)
- ETFs (e.g., SPY, QQQ)
- Cryptocurrencies (e.g., BTC-USD, ETH-USD)
- Futures (e.g., GC=F, CL=F)
- Indices (e.g., ^GSPC for S&P 500)

## Settings

Access settings via the settings button (top-right toolbar):

- **News Tickers**: Configure which tickers to monitor for news
  - In View Mode 3, only news from your watchlist is shown
  - In other modes, news from configured tickers is shown

## Keyboard Shortcuts

- **Tab**: Move focus between widgets
- **Enter**: Add selected search result to watchlist
- **Delete/Backspace**: Remove selected asset from watchlist (when focused)

## Troubleshooting

### Application Won't Start

**Error: "spinner.gif not found"**
- Download a spinner animation from the internet
- Save it as `spinner.gif` in the project directory
- Or create a simple animated GIF

**Error: DLL initialization failed (PyTorch)**
- This is expected if PyTorch isn't installed correctly
- The application will still work without AI features
- News will display without trading signals

**Error: "Impossibile trovare il file 'news.py'"**
- Make sure `news.py` is in the same directory as `graph.py`
- This file is required for the application to work

### Charts Not Loading

- Check your internet connection
- Verify the ticker symbol is correct
- Some tickers may not have data available
- Try a different timeframe

### News Not Appearing

- Check your internet connection
- News updates every 5 minutes - wait for the next update
- In View Mode 3, make sure you have assets in your watchlist
- Verify the news tickers are configured in settings

### AI Analysis Not Working

- Ensure `model.py` exists in the project directory
- Install PyTorch and transformers: `pip install torch transformers`
- The first time loading the model may take several minutes
- If model loading fails, the app will continue without AI features
- Check the console for error messages

## File Structure

```
TheSentient/
├── graph.py           # Main application
├── news.py            # News fetching module
├── settings_view.py   # UI components
├── rsi.py            # RSI indicator (optional)
├── model.py          # AI analysis (optional)
├── settings.json     # Application settings (auto-generated)
├── watchlist.json    # Watchlist data (auto-generated)
├── spinner.gif       # Loading animation
├── icon.ico          # Application icon
└── README.md         # This file
```

## Tips & Best Practices

1. **Start with View Mode 1** for a clean charting experience
2. **Use View Mode 3** when you want to monitor news without distractions
3. **Add your most important assets** to the watchlist for focused news in View Mode 3
4. **Check news regularly** - the flyout panel makes it easy to stay informed
5. **Use AI signals as guidance** - always verify with your own analysis
6. **Save your watchlist** - it's automatically saved, but you can backup `settings.json`

## Technical Details

- **Data Source**: Yahoo Finance (via yfinance library)
- **News Source**: Yahoo Finance News API
- **Charting Library**: mplfinance and matplotlib
- **UI Framework**: PyQt6
- **AI Model**: DeepSeek Coder 1.3B (optional, for trading signal analysis)

## License & Disclaimer

**DISCLAIMER**: This software is for educational and informational purposes only. 

- **NOT FINANCIAL ADVICE**: Trading signals and analysis are not financial advice
- **DO YOUR OWN RESEARCH**: Always conduct your own research before making trading decisions
- **RISK WARNING**: Trading involves risk of loss. Never invest more than you can afford to lose
- **NO WARRANTIES**: The software is provided "as is" without warranties of any kind

## Support

For issues, questions, or contributions:
1. Check the troubleshooting section above
2. Review error messages in the console
3. Ensure all required files are present
4. Verify internet connectivity for data fetching

## Version History

- **Current Version**: Includes modern UI, AI analysis, flyout news panel, and multiple view modes

---

**Enjoy using The Sentient!** 📊📰🤖

