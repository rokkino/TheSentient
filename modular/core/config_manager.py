"""
Configuration Manager - Centralized configuration management for modules.
"""
import json
import os
from typing import Dict, Any, Optional
import yaml
from pathlib import Path


class ConfigManager:
    """Manages configuration for the modular system."""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self._configs: Dict[str, Dict[str, Any]] = {}
        self._defaults = {
            "system": {
                "name": "The Sentient Trading System",
                "version": "1.0.0",
                "debug": False,
                "log_level": "INFO"
            },
            "modules": {
                "news": {"enabled": True, "auto_refresh": True, "refresh_interval": 300},
                "bot": {"enabled": True, "max_bots": 10},
                "strategy": {"enabled": True},
                "earnings": {"enabled": True},
                "backtesting": {"enabled": True},
                "stocks": {"enabled": True},
                "graph": {"enabled": True}
            },
            "database": {
                "path": "data/databases/thesentient.db",
                "type": "sqlite"
            },
            "api": {
                "host": "localhost",
                "port": 8000,
                "cors_origins": ["http://localhost:5173"]
            }
        }
        
        # Ensure config directory exists
        self.config_dir.mkdir(exist_ok=True)
        
    def load_config(self, name: str, filepath: Optional[str] = None) -> Dict[str, Any]:
        """Load configuration from file."""
        if filepath is None:
            filepath = self.config_dir / f"{name}.json"
        else:
            filepath = Path(filepath)
            
        config = self._defaults.get(name, {}).copy()
        
        if filepath.exists():
            try:
                with open(filepath, 'r') as f:
                    if filepath.suffix == '.json':
                        loaded = json.load(f)
                    elif filepath.suffix in ['.yaml', '.yml']:
                        loaded = yaml.safe_load(f)
                    else:
                        # Try JSON first, then YAML
                        try:
                            loaded = json.load(f)
                        except json.JSONDecodeError:
                            f.seek(0)
                            loaded = yaml.safe_load(f)
                    
                    # Merge with defaults (deep merge)
                    self._deep_merge(config, loaded)
            except Exception as e:
                print(f"Error loading config {filepath}: {e}")
        
        self._configs[name] = config
        return config
        
    def save_config(self, name: str, config: Dict[str, Any], filepath: Optional[str] = None):
        """Save configuration to file."""
        if filepath is None:
            filepath = self.config_dir / f"{name}.json"
        else:
            filepath = Path(filepath)
            
        # Ensure directory exists
        filepath.parent.mkdir(exist_ok=True)
        
        try:
            with open(filepath, 'w') as f:
                if filepath.suffix == '.json':
                    json.dump(config, f, indent=2)
                elif filepath.suffix in ['.yaml', '.yml']:
                    yaml.dump(config, f, default_flow_style=False)
                else:
                    # Default to JSON
                    json.dump(config, f, indent=2)
                    
            self._configs[name] = config
            print(f"Saved config {name} to {filepath}")
        except Exception as e:
            print(f"Error saving config {filepath}: {e}")
            
    def get_config(self, name: str, key: Optional[str] = None, default: Any = None) -> Any:
        """Get configuration value."""
        if name not in self._configs:
            self.load_config(name)
            
        config = self._configs.get(name, {})
        
        if key is None:
            return config
            
        # Support dot notation for nested keys
        if '.' in key:
            keys = key.split('.')
            value = config
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            return value
        else:
            return config.get(key, default)
            
    def set_config(self, name: str, key: str, value: Any):
        """Set configuration value."""
        if name not in self._configs:
            self._configs[name] = self._defaults.get(name, {}).copy()
            
        config = self._configs[name]
        
        # Support dot notation for nested keys
        if '.' in key:
            keys = key.split('.')
            current = config
            for k in keys[:-1]:
                if k not in current or not isinstance(current[k], dict):
                    current[k] = {}
                current = current[k]
            current[keys[-1]] = value
        else:
            config[key] = value
            
    def get_module_config(self, module_name: str) -> Dict[str, Any]:
        """Get configuration for a specific module."""
        modules_config = self.get_config("modules")
        if not isinstance(modules_config, dict):
            modules_config = {}
        
        module_config = modules_config.get(module_name, {})
        
        # Merge with module-specific config file if exists
        module_file = self.config_dir / f"module_{module_name}.json"
        if module_file.exists():
            try:
                with open(module_file, 'r') as f:
                    file_config = json.load(f)
                    self._deep_merge(module_config, file_config)
            except Exception as e:
                print(f"Error loading module config {module_file}: {e}")
                
        return module_config
        
    def reload_all(self):
        """Reload all configurations from disk."""
        for name in self._configs.keys():
            self.load_config(name)
            
    def _deep_merge(self, target: Dict, source: Dict):
        """Deep merge source into target."""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_merge(target[key], value)
            else:
                target[key] = value


# Global config manager instance
_config_manager = None

def get_config_manager(config_dir: str = "config") -> ConfigManager:
    """Get or create the global configuration manager."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager(config_dir)
    return _config_manager