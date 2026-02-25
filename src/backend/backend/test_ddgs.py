try:
    from duckduckgo_search import DDGS
    print("Import successful: duckduckgo_search")
except ImportError:
    try:
        from ddgs import DDGS
        print("Import successful: ddgs")
    except ImportError:
        print("Import failed: neither duckduckgo_search nor ddgs found")
        exit(1)

try:
    ddgs = DDGS()
    print("Initialization successful")
    results = ddgs.text("python", max_results=1)
    print(f"Search test: {results}")
except Exception as e:
    print(f"Initialization or search failed: {e}")
