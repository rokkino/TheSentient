import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the current directory to sys.path to allow imports from backend
sys.path.append(os.getcwd())

from backend.services.ig_service import IGMarketsService
import config

async def verify_ig():
    print("--- Verifying IG Trading Connection ---")
    
    # Load environment variables
    load_dotenv()
    
    # Get credentials from config or env
    username = config.IG_USERNAME or os.getenv("IG_USERNAME")
    password = config.IG_PASSWORD or os.getenv("IG_PASSWORD")
    api_key = config.IG_API_KEY or os.getenv("IG_API_KEY")
    acc_type = config.IG_ACC_TYPE or os.getenv("IG_ACC_TYPE", "DEMO")
    
    print(f"Username: {username}")
    print(f"Account Type: {acc_type}")
    if api_key:
        print("API Key: [PRESENT]")
    else:
        print("API Key: [MISSING]")
        
    if not username or not password or not api_key:
        print("Error: Missing credentials. Please check config.py or .env file.")
        return

    try:
        ig_service = IGMarketsService(
            username=username,
            password=password,
            api_key=api_key,
            acc_type=acc_type
        )
        
        if not ig_service.is_configured():
            print("IG Service not configured properly.")
            return

        print("\nAttempting to fetch account details...")
        account = await ig_service.get_account()
        
        if account:
            print("\n--- Account Details ---")
            for key, value in account.items():
                print(f"{key}: {value}")
            print("\nConnection Successful!")
        else:
            print("\nFailed to fetch account details.")

    except Exception as e:
        print(f"\nError during verification: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_ig())
