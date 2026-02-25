"""
Event Bus - Publish/subscribe system for inter-module communication.
"""
import asyncio
from typing import Dict, List, Callable, Any, Optional
import logging


class EventBus:
    """Event bus for module communication."""
    
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._logger = logging.getLogger(__name__)
        
    def subscribe(self, event_type: str, callback: Callable):
        """Subscribe to an event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)
        self._logger.debug(f"Subscribed {callback} to event '{event_type}'")
        
    def unsubscribe(self, event_type: str, callback: Callable):
        """Unsubscribe from an event type."""
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(callback)
                self._logger.debug(f"Unsubscribed {callback} from event '{event_type}'")
            except ValueError:
                pass
                
    def publish(self, event_type: str, data: Optional[dict] = None):
        """Publish an event synchronously."""
        if data is None:
            data = {}
            
        self._logger.debug(f"Publishing event '{event_type}' with data: {data}")
        
        if event_type in self._subscribers:
            for callback in self._subscribers[event_type]:
                try:
                    callback(event_type, data)
                except Exception as e:
                    self._logger.error(f"Error in event handler for '{event_type}': {e}")
                    
    async def publish_async(self, event_type: str, data: Optional[dict] = None):
        """Publish an event asynchronously."""
        if data is None:
            data = {}
            
        self._logger.debug(f"Publishing async event '{event_type}' with data: {data}")
        
        if event_type in self._subscribers:
            tasks = []
            for callback in self._subscribers[event_type]:
                tasks.append(self._call_async_handler(callback, event_type, data))
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
                
    async def _call_async_handler(self, callback: Callable, event_type: str, data: dict):
        """Call an async handler safely."""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(event_type, data)
            else:
                callback(event_type, data)
        except Exception as e:
            self._logger.error(f"Error in async event handler for '{event_type}': {e}")
            
    def get_subscriber_count(self, event_type: str) -> int:
        """Get number of subscribers for an event type."""
        return len(self._subscribers.get(event_type, []))
        
    def clear_subscribers(self, event_type: Optional[str] = None):
        """Clear subscribers for an event type or all events."""
        if event_type is None:
            self._subscribers.clear()
            self._logger.debug("Cleared all subscribers")
        elif event_type in self._subscribers:
            self._subscribers[event_type].clear()
            self._logger.debug(f"Cleared subscribers for event '{event_type}'")


# Global event bus instance
_event_bus = None

def get_event_bus() -> EventBus:
    """Get or create the global event bus."""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


# Common event types
class EventTypes:
    """Standard event types for the system."""
    
    # Module lifecycle
    MODULE_INITIALIZED = "module.initialized"
    MODULE_SHUTDOWN = "module.shutdown"
    
    # Data events
    MARKET_DATA_UPDATED = "market_data.updated"
    NEWS_RECEIVED = "news.received"
    EARNINGS_ANNOUNCED = "earnings.announced"
    
    # Trading events
    ORDER_PLACED = "order.placed"
    ORDER_FILLED = "order.filled"
    POSITION_UPDATED = "position.updated"
    
    # Bot events
    BOT_CREATED = "bot.created"
    BOT_ACTIVATED = "bot.activated"
    BOT_DEACTIVATED = "bot.deactivated"
    
    # UI events
    TAB_SWITCHED = "ui.tab_switched"
    NOTIFICATION_SHOW = "ui.notification_show"
    
    # System events
    ERROR_OCCURRED = "system.error"
    CONFIG_UPDATED = "system.config_updated"