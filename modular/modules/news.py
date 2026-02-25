"""
News Module - Modular implementation of news functionality.
"""
import sys
import os
from typing import Dict, Any, List
from fastapi import APIRouter

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from modular.core.module_registry import ModuleInterface
from modular.core.event_bus import get_event_bus, EventTypes


class NewsModule(ModuleInterface):
    """News module implementing the ModuleInterface."""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.name = "news"
        self.version = "1.0.0"
        self.enabled = config.get("enabled", True)
        self.auto_refresh = config.get("auto_refresh", True)
        self.refresh_interval = config.get("refresh_interval", 300)
        
        # Initialize components
        self.router = APIRouter(prefix="/api/news", tags=["news"])
        self._setup_routes()
        
        # Lazy load of existing news service
        self._news_service = None
        self._event_bus = get_event_bus()
        
    def _get_news_service(self):
        """Lazy load the existing news service."""
        if self._news_service is None:
            try:
                # Import the existing news service
                from src.backend.backend.services.news_service import NewsService
                self._news_service = NewsService()
                print(f"[NewsModule] Loaded existing NewsService")
            except ImportError as e:
                print(f"[NewsModule] Could not import NewsService: {e}")
                # Create a simple stub
                self._news_service = self._create_stub_service()
        return self._news_service
        
    def _create_stub_service(self):
        """Create a stub service for testing."""
        class StubNewsService:
            def __init__(self):
                self.seen_links = set()
                self.is_monitoring = False
                
            async def fetch_news(self, limit=20):
                return [
                    {
                        "title": "Sample News - Modular System Active",
                        "link": "https://example.com",
                        "summary": "The modular news system is functioning correctly.",
                        "published": "2026-02-19T12:00:00Z",
                        "source": "System"
                    }
                ]
                
            async def analyze_sentiment(self, news_item):
                return {"sentiment": "neutral", "assets": []}
                
            def start_monitoring(self):
                self.is_monitoring = True
                return True
                
            def stop_monitoring(self):
                self.is_monitoring = False
                return True
                
        return StubNewsService()
        
    def _setup_routes(self):
        """Setup FastAPI routes for this module."""
        
        @self.router.get("/")
        async def get_news(limit: int = 20):
            """Get latest news."""
            service = self._get_news_service()
            news = await service.fetch_news(limit=limit)
            return {"news": news, "module": self.name}
            
        @self.router.get("/monitoring/status")
        async def get_monitoring_status():
            """Get monitoring status."""
            service = self._get_news_service()
            return {
                "monitoring": service.is_monitoring,
                "enabled": self.enabled,
                "auto_refresh": self.auto_refresh
            }
            
        @self.router.post("/monitoring/start")
        async def start_monitoring():
            """Start news monitoring."""
            service = self._get_news_service()
            success = service.start_monitoring()
            
            # Publish event
            self._event_bus.publish(
                EventTypes.NEWS_RECEIVED,
                {"action": "monitoring_started", "success": success}
            )
            
            return {"success": success, "message": "Monitoring started"}
            
        @self.router.post("/monitoring/stop")
        async def stop_monitoring():
            """Stop news monitoring."""
            service = self._get_news_service()
            success = service.stop_monitoring()
            
            # Publish event
            self._event_bus.publish(
                EventTypes.NEWS_RECEIVED,
                {"action": "monitoring_stopped", "success": success}
            )
            
            return {"success": success, "message": "Monitoring stopped"}
            
        @self.router.get("/sentiment/{news_id}")
        async def analyze_sentiment(news_id: str):
            """Analyze sentiment for a news item."""
            service = self._get_news_service()
            # In a real implementation, we'd fetch the news item by ID
            # For now, create a dummy item
            news_item = {"title": "Sample news", "text": "Sample content"}
            sentiment = await service.analyze_sentiment(news_item)
            return {"news_id": news_id, "sentiment": sentiment}
            
    def initialize(self) -> bool:
        """Initialize the news module."""
        if not self.enabled:
            print(f"[NewsModule] Module disabled")
            return False
            
        try:
            # Load the service
            service = self._get_news_service()
            
            # Subscribe to events
            self._event_bus.subscribe(EventTypes.MARKET_DATA_UPDATED, self._on_market_data)
            self._event_bus.subscribe(EventTypes.CONFIG_UPDATED, self._on_config_updated)
            
            print(f"[NewsModule] Initialized successfully")
            
            # Start monitoring if auto_refresh is enabled
            if self.auto_refresh:
                service.start_monitoring()
                print(f"[NewsModule] Auto-refresh enabled (interval: {self.refresh_interval}s)")
                
            return True
        except Exception as e:
            print(f"[NewsModule] Initialization failed: {e}")
            return False
            
    def shutdown(self):
        """Shutdown the news module."""
        try:
            service = self._get_news_service()
            if service.is_monitoring:
                service.stop_monitoring()
                
            # Unsubscribe from events
            self._event_bus.unsubscribe(EventTypes.MARKET_DATA_UPDATED, self._on_market_data)
            self._event_bus.unsubscribe(EventTypes.CONFIG_UPDATED, self._on_config_updated)
            
            print(f"[NewsModule] Shutdown complete")
        except Exception as e:
            print(f"[NewsModule] Error during shutdown: {e}")
            
    def get_state(self) -> dict:
        """Return current module state."""
        service = self._get_news_service()
        return {
            "name": self.name,
            "version": self.version,
            "enabled": self.enabled,
            "monitoring": service.is_monitoring,
            "auto_refresh": self.auto_refresh,
            "refresh_interval": self.refresh_interval,
            "news_count": len(service.seen_links) if hasattr(service, 'seen_links') else 0
        }
        
    def handle_event(self, event_type: str, data: dict):
        """Handle events from other modules."""
        print(f"[NewsModule] Received event: {event_type}")
        
        if event_type == EventTypes.MARKET_DATA_UPDATED:
            self._on_market_data(event_type, data)
        elif event_type == EventTypes.CONFIG_UPDATED:
            self._on_config_updated(event_type, data)
        elif event_type == "news.fetch_request":
            # Handle fetch request
            self._on_fetch_request(data)
            
    def get_api_routes(self) -> list:
        """Return FastAPI routes for this module."""
        return [self.router]
        
    # Event handlers
    def _on_market_data(self, event_type: str, data: dict):
        """Handle market data updates."""
        # In a real implementation, we might want to fetch news related to
        # specific symbols when market data changes
        symbols = data.get("symbols", [])
        if symbols:
            print(f"[NewsModule] Market data updated for symbols: {symbols}")
            # Could trigger news fetch for these symbols
            
    def _on_config_updated(self, event_type: str, data: dict):
        """Handle configuration updates."""
        news_config = data.get("modules", {}).get("news", {})
        if news_config:
            # Update module configuration
            self.enabled = news_config.get("enabled", self.enabled)
            self.auto_refresh = news_config.get("auto_refresh", self.auto_refresh)
            self.refresh_interval = news_config.get("refresh_interval", self.refresh_interval)
            print(f"[NewsModule] Configuration updated")
            
    def _on_fetch_request(self, data: dict):
        """Handle fetch requests."""
        symbols = data.get("symbols", [])
        limit = data.get("limit", 10)
        print(f"[NewsModule] Fetch request for symbols: {symbols}")
        # Implementation would fetch news for specific symbols
        
    # Additional module-specific methods
    async def fetch_latest_news(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Fetch latest news (public API)."""
        service = self._get_news_service()
        return await service.fetch_news(limit=limit)
        
    async def analyze_news_sentiment(self, news_item: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze sentiment of a news item (public API)."""
        service = self._get_news_service()
        return await service.analyze_sentiment(news_item)