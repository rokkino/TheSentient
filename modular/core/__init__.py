"""
Core framework for modular system.
"""
from .module_registry import ModuleRegistry
from .event_bus import EventBus
from .config_manager import ConfigManager

__all__ = ["ModuleRegistry", "EventBus", "ConfigManager"]