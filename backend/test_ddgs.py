from duckduckgo_search import DDGS
print("Import successful")
try:
    ddgs = DDGS()
    print("Initialization successful")
except Exception as e:
    print(f"Initialization failed: {e}")
