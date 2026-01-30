import os
import sys
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

# Load env variables
load_dotenv()

def verify_alpaca_env():
    print("--- Verifying Alpaca Environment Variables ---")
    
    base_url = os.getenv('ALPACA_BASE_URL')
    api_key = os.getenv('ALPACA_API_KEY')
    api_secret = os.getenv('ALPACA_API_SECRET')
    
    print(f"ALPACA_BASE_URL: {base_url}")
    print(f"ALPACA_API_KEY: {api_key}")
    print(f"ALPACA_API_SECRET: {api_secret if api_secret else '(empty)'}")
    
    if api_key and base_url and not api_secret:
        print("\nWARNING: Secret Key is missing. Alpaca Service will likely fail.")
    
    print("\n--- Testing AlpacaService Initialization ---")
    try:
        from services.alpaca_service import AlpacaService
        service = AlpacaService()
        configured = service.is_configured()
        print(f"AlpacaService.is_configured(): {configured}")
        
    except ImportError:
        print("Could not import AlpacaService. Check path.")
    except Exception as e:
        print(f"Error initializing AlpacaService: {e}")

if __name__ == "__main__":
    verify_alpaca_env()
