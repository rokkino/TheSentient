import os
import sys
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

# Load env
load_dotenv()

def verify_env():
    print("--- Verifying Environment Variables ---")
    
    # Check raw env vars
    ig_user = os.getenv('IG_USERNAME')
    google_key = os.getenv('GOOGLE_API_KEY')
    
    print(f"IG_USERNAME present: {bool(ig_user)}")
    print(f"GOOGLE_API_KEY present: {bool(google_key)}")
    
    if not ig_user or not google_key:
        print("ERROR: Missing environment variables!")
        return

    print("\n--- Verifying Service Initialization ---")
    
    try:
        from src.backend.services.ig_service import IGMarketsService
        # Initialize without args - should pick up from env
        ig = IGMarketsService()
        print(f"IG Service Configured: {ig.is_configured()}")
        if ig.is_configured():
            print(f"IG User: {ig.username}")
            print(f"IG Account Type: {ig.acc_type}")
        else:
            print("IG Service failed to configure from env.")
            
    except Exception as e:
        print(f"Error testing IG Service: {e}")

    try:
        from src.backend.services.gemini_service import GeminiService
        # Initialize without args
        gemini = GeminiService()
        print(f"Gemini Service Available: {gemini.available}")
        
    except Exception as e:
        print(f"Error testing Gemini Service: {e}")

if __name__ == "__main__":
    verify_env()
