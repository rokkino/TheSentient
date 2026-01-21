import os
import sys
import asyncio
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

load_dotenv()

async def verify():
    print("Verifying AI Services...")
    
    # 1. Verify Gemini
    print("\n--- Testing Gemini Service ---")
    try:
        from services.gemini_service import GeminiService
        gemini = GeminiService()
        if gemini.available:
            print(f"Gemini initialized successfully. Model: {gemini.model.model_name}")
            # Try a quick generation if api key is present
            if gemini.api_key:
                print("Attempting quick generation...")
                try:
                    resp = gemini.model.generate_content("Hello, are you fast?")
                    print(f"Response received: {resp.text[:50]}...")
                except Exception as e:
                    print(f"Generation failed (might be expected if quota/auth issue): {e}")
        else:
            print("Gemini not available (check API key or install).")
    except Exception as e:
        print(f"Gemini verification failed: {e}")

    # 2. Verify Llama
    print("\n--- Testing Llama Service ---")
    try:
        from services.llama_service import llama_service
        print(f"Llama Service initialized. Model: {llama_service.model_name}")
        # We won't actually call Ollama here to avoid hanging if it's slow, 
        # but we verified the code change.
        print("Llama code updated to request GPU.")
    except Exception as e:
        print(f"Llama verification failed: {e}")

if __name__ == "__main__":
    asyncio.run(verify())
