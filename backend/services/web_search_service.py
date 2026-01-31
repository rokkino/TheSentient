"""
Web Search Service - Handles internet search using DuckDuckGo
"""
import warnings
from typing import List, Dict, Any

with warnings.catch_warnings():
    warnings.simplefilter("ignore", RuntimeWarning)
    from duckduckgo_search import DDGS

class WebSearchService:
    def __init__(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            self.ddgs = DDGS()

    def search(self, query: str, max_results: int = 3) -> str:
        """
        Perform a web search and return a formatted string of results.
        """
        try:
            results = self.ddgs.text(query, max_results=max_results)
            if not results:
                return "No search results found."
            
            formatted_results = "Web Search Results:\n"
            for i, result in enumerate(results, 1):
                title = result.get('title', 'No Title')
                body = result.get('body', 'No Content')
                href = result.get('href', '#')
                formatted_results += f"{i}. {title}\n   {body}\n   Source: {href}\n\n"
            
            return formatted_results
        except Exception as e:
            print(f"[WebSearchService] Error performing search: {e}")
            return f"Error performing web search: {str(e)}"

# Singleton instance
web_search_service = WebSearchService()
