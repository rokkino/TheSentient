import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    from google import genai
    print("Import successful: google.genai")
except ImportError:
    print("Import failed: google.genai")
    exit(1)

api_key = os.getenv('GOOGLE_GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
if not api_key:
    print("Error: API key not found")
    exit(1)

try:
    client = genai.Client(api_key=api_key)
    print("Client initialized")
    
    response = client.models.generate_content(
        model='gemini-3.0-flash',
        contents='Hello, are you working?'
    )
    print(f"Response received: {response.text}")
    print("Verification successful!")
except Exception as e:
    print(f"Verification failed: {e}")
