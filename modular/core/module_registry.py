"""
Module Registry - Central registry for managing modular components.
"""
import importlib
import inspect
from typing import Dict, List, Any, Optional, Type
from abc import ABC, abstractmethod


class ModuleInterface(ABC):
    """Base interface for all tab modules."""
    
    def __init__(self, config: dict):
        self.config = config
        self.name = ""
        self.version = "1.0.0"
        
    @abstractmethod
    def initialize(self) -> bool:
        """Initialize module resources."""
        pass
        
    @abstractmethod
    def shutdown(self):
        """Clean up resources."""
        pass
        
    @abstractmethod
    def get_state(self) -> dict:
        """Return current module state for frontend."""
        pass
        
    @abstractmethod
    def handle_event(self, event_type: str, data: dict):
        """Handle events from other modules."""
        pass
        
    @abstractmethod
    def get_api_routes(self) -> list:
        """Return FastAPI routes for this module."""
        pass


class ModuleRegistry:
    """Registry for managing modules."""
    
    def __init__(self):
        self._modules: Dict[str, ModuleInterface] = {}
        self._module_classes: Dict[str, Type[ModuleInterface]] = {}
        
    def register_class(self, name: str, module_class: Type[ModuleInterface]):
        """Register a module class by name."""
        self._module_classes[name] = module_class
        
    def create_instance(self, name: str, config: dict) -> ModuleInterface:
        """Create an instance of a registered module."""
        if name not in self._module_classes:
            raise ValueError(f"Module '{name}' not registered")
        module = self._module_classes[name](config)
        module.name = name
        return module
        
    def register_instance(self, name: str, instance: ModuleInterface):
        """Register a module instance."""
        self._modules[name] = instance
        
    def get_instance(self, name: str) -> Optional[ModuleInterface]:
        """Get a module instance by name."""
        return self._modules.get(name)
        
    def initialize_all(self):
        """Initialize all registered module instances."""
        for name, module in self._modules.items():
            if module.initialize():
                print(f"Module '{name}' initialized successfully")
            else:
                print(f"Module '{name}' failed to initialize")
                
    def shutdown_all(self):
        """Shutdown all registered module instances."""
        for name, module in self._modules.items():
            module.shutdown()
            print(f"Module '{name}' shut down")
            
    def get_all_states(self) -> Dict[str, dict]:
        """Get state from all modules."""
        return {name: module.get_state() for name, module in self._modules.items()}
        
    def broadcast_event(self, event_type: str, data: dict):
        """Broadcast an event to all modules."""
        for name, module in self._modules.items():
            try:
                module.handle_event(event_type, data)
            except Exception as e:
                print(f"Error handling event in module '{name}': {e}")
                
    def discover_modules(self, package_path: str = "modular.modules"):
        """Discover module classes in a package."""
        try:
            package = importlib.import_module(package_path)
            for name in dir(package):
                obj = getattr(package, name)
                if (inspect.isclass(obj) and 
                    issubclass(obj, ModuleInterface) and 
                    obj != ModuleInterface):
                    self.register_class(obj.__name__, obj)
                    print(f"Discovered module class: {obj.__name__}")
        except ImportError as e:
            print(f"Could not discover modules from {package_path}: {e}")
            
    def load_from_config(self, config: dict):
        """Load modules from configuration dictionary."""
        modules_config = config.get("modules", {})
        for name, module_config in modules_config.items():
            if name in self._module_classes:
                instance = self.create_instance(name, module_config)
                self.register_instance(name, instance)
                print(f"Loaded module: {name}")
            else:
                print(f"Warning: Module '{name}' not found in registry")


# Global registry instance
_registry = None

def get_registry() -> ModuleRegistry:
    """Get or create the global module registry."""
    global _registry
    if _registry is None:
        _registry = ModuleRegistry()
    return _registry