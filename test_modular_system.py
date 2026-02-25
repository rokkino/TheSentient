#!/usr/bin/env python3
"""
Test the modular system with core framework and news module.
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_core_framework():
    """Test core framework components."""
    print("=== Testing Core Framework ===")
    
    try:
        from modular.core.module_registry import ModuleRegistry, ModuleInterface, get_registry
        from modular.core.event_bus import EventBus, get_event_bus, EventTypes
        from modular.core.config_manager import ConfigManager, get_config_manager
        
        print("PASS Core imports successful")
        
        # Test registry
        registry = ModuleRegistry()
        print(f"PASS ModuleRegistry created: {registry}")
        
        # Test event bus
        event_bus = get_event_bus()
        print(f"PASS EventBus created: {event_bus}")
        
        # Test config manager
        config_manager = get_config_manager("config")
        print(f"PASS ConfigManager created: {config_manager}")
        
        # Load system config
        system_config = config_manager.load_config("system")
        print(f"PASS System config loaded: {system_config.get('name')}")
        
        return True
    except Exception as e:
        print(f"FAIL Core framework test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_news_module():
    """Test news module integration."""
    print("\n=== Testing News Module ===")
    
    try:
        from modular.modules.news import NewsModule
        from modular.core.module_registry import get_registry
        from modular.core.config_manager import get_config_manager
        
        # Get config
        config_manager = get_config_manager()
        module_config = config_manager.get_module_config("news")
        print(f"PASS News module config: {module_config}")
        
        # Create module instance
        news_module = NewsModule(module_config)
        print(f"PASS NewsModule created: {news_module.name} v{news_module.version}")
        
        # Test initialization
        initialized = news_module.initialize()
        print(f"PASS NewsModule initialized: {initialized}")
        
        # Test state
        state = news_module.get_state()
        print(f"PASS NewsModule state: {state}")
        
        # Test API routes
        routes = news_module.get_api_routes()
        print(f"PASS NewsModule API routes: {len(routes)} route(s)")
        
        # Test shutdown
        news_module.shutdown()
        print("PASS NewsModule shutdown")
        
        return True
    except Exception as e:
        print(f"FAIL News module test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_module_registry_integration():
    """Test module registry integration."""
    print("\n=== Testing Module Registry Integration ===")
    
    try:
        from modular.core.module_registry import get_registry
        from modular.modules.news import NewsModule
        from modular.core.config_manager import get_config_manager
        
        registry = get_registry()
        config_manager = get_config_manager()
        
        # Register news module class
        registry.register_class("news", NewsModule)
        print("PASS NewsModule class registered")
        
        # Discover modules
        registry.discover_modules("modular.modules")
        print("PASS Module discovery completed")
        
        # Create and register instance
        module_config = config_manager.get_module_config("news")
        news_instance = registry.create_instance("news", module_config)
        registry.register_instance("news", news_instance)
        print(f"PASS NewsModule instance registered: {news_instance.name}")
        
        # Initialize all modules
        registry.initialize_all()
        print("PASS All modules initialized")
        
        # Get all states
        states = registry.get_all_states()
        print(f"PASS Module states: {list(states.keys())}")
        
        # Broadcast event
        registry.broadcast_event(EventTypes.CONFIG_UPDATED, {"test": True})
        print("PASS Event broadcast")
        
        # Shutdown
        registry.shutdown_all()
        print("PASS All modules shutdown")
        
        return True
    except Exception as e:
        print(f"FAIL Registry integration test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_event_bus_functionality():
    """Test event bus functionality."""
    print("\n=== Testing Event Bus ===")
    
    try:
        from modular.core.event_bus import get_event_bus, EventTypes
        
        event_bus = get_event_bus()
        
        # Test subscription
        def test_handler(event_type, data):
            print(f"  Event received: {event_type} -> {data}")
            
        event_bus.subscribe(EventTypes.NEWS_RECEIVED, test_handler)
        print(f"PASS Subscribed to {EventTypes.NEWS_RECEIVED}")
        
        # Test publishing
        event_bus.publish(EventTypes.NEWS_RECEIVED, {"test": "data"})
        print("PASS Event published")
        
        # Test subscriber count
        count = event_bus.get_subscriber_count(EventTypes.NEWS_RECEIVED)
        print(f"PASS Subscriber count: {count}")
        
        # Test unsubscribe
        event_bus.unsubscribe(EventTypes.NEWS_RECEIVED, test_handler)
        print("PASS Unsubscribed")
        
        # Test clear
        event_bus.clear_subscribers()
        print("PASS All subscribers cleared")
        
        return True
    except Exception as e:
        print(f"FAIL Event bus test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_configuration():
    """Test configuration management."""
    print("\n=== Testing Configuration ===")
    
    try:
        from modular.core.config_manager import get_config_manager
        
        config_manager = get_config_manager()
        
        # Test system config
        system_config = config_manager.get_config("system")
        print(f"PASS System config: {system_config.get('name')}")
        
        # Test module config
        news_config = config_manager.get_module_config("news")
        print(f"PASS News module config: {news_config}")
        
        # Test setting config
        config_manager.set_config("test", "key", "value")
        value = config_manager.get_config("test", "key")
        print(f"PASS Set/get config: {value}")
        
        # Test nested keys
        config_manager.set_config("test", "nested.key", "nested_value")
        nested = config_manager.get_config("test", "nested.key")
        print(f"PASS Nested config: {nested}")
        
        # Save config
        config_manager.save_config("test", {"key": "value", "nested": {"key": "nested_value"}})
        print("PASS Config saved")
        
        # Reload
        config_manager.reload_all()
        print("PASS Configs reloaded")
        
        return True
    except Exception as e:
        print(f"FAIL Configuration test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("Starting Modular System Tests")
    print("=" * 50)
    
    results = []
    
    results.append(("Core Framework", test_core_framework()))
    results.append(("Configuration", test_configuration()))
    results.append(("Event Bus", test_event_bus_functionality()))
    results.append(("News Module", test_news_module()))
    results.append(("Registry Integration", test_module_registry_integration()))
    
    print("\n" + "=" * 50)
    print("Test Results:")
    print("=" * 50)
    
    all_passed = True
    for test_name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"{status} {test_name}")
        if not passed:
            all_passed = False
            
    print("=" * 50)
    if all_passed:
        print("SUCCESS: All modular system tests passed!")
    else:
        print("FAILURE: Some tests failed.")
        
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)