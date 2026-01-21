import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- Configuration Constants ---

# IG Markets
# You can directly paste your keys here if you prefer not to use .env
IG_USERNAME = os.getenv("IG_USERNAME", "your_username_here")
IG_PASSWORD = os.getenv("IG_PASSWORD", "your_password_here")
IG_API_KEY = os.getenv("IG_API_KEY", "your_api_key_here")
IG_ACC_TYPE = os.getenv("IG_ACC_TYPE", "DEMO")
IG_ACC_NUMBER = os.getenv("IG_ACC_NUMBER", "your_acc_number_here")

# Google Gemini
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "your_google_api_key_here")

# Ollama
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:1b")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# Trading Parameters
MAX_RISK_PER_TRADE = 0.01  # 1% of equity
MAX_SPREAD_PIPS = 5.0
SLEEP_INTERVAL_SECONDS = 60

# --- System Prompts ---

MANAGER_SYSTEM_PROMPT = """You are the Trade Execution Manager. Current Time: {time}. Market Status: {status}.
Rules:
- If Weekend (Sat/Sun): Output JSON {{"action": "SLEEP"}}
- If Night (22:00 - 08:00 CET): Output JSON {{"action": "SLEEP"}}
- If Pre-Market (14:00 CET) or Earnings release: Output JSON {{"action": "ACTIVATE_ANALYST", "context": "..."}}
- If Open Positions exist: Output JSON {{"action": "ACTIVATE_ANALYST", "context": "CHECK_STOPS"}}
"""

ANALYST_SYSTEM_PROMPT = """You are a Risk-Averse Quantitative Trader. Strategy: Mean Reversion & Earnings Momentum.
Input Data: {data}.
Task: Decide trade.
Constraints: Max Risk 1% of equity.
Output JSON STRICTLY:
{{
  "decision": "BUY" | "SELL" | "PASS",
  "ticker": "...",
  "entry_price": float,
  "stop_loss": float,
  "take_profit": float,
  "size": int,
  "reason": "string"
}}
"""
