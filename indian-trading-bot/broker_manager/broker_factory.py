from typing import Dict, Optional, Type, List
import importlib
import os
from broker_manager.base_broker import BaseBrokerInterface
from utils.logging import get_logger

logger = get_logger(__name__)

class BrokerFactory:
    """
    Factory class for creating broker instances dynamically.
    Supports plugin-style broker loading similar to OpenAlgo architecture.
    """
    
    _registered_brokers: Dict[str, Type[BaseBrokerInterface]] = {}
    _broker_configs: Dict[str, Dict] = {}
    
    @classmethod
    def register_broker(cls, broker_name: str, broker_class: Type[BaseBrokerInterface], 
                       config: Optional[Dict] = None):
        """
        Register a broker class with the factory
        Args:
            broker_name: Unique name for the broker (e.g., 'dhan', 'zerodha')
            broker_class: Broker implementation class
            config: Optional configuration dict
        """
        cls._registered_brokers[broker_name.lower()] = broker_class
        cls._broker_configs[broker_name.lower()] = config or {}
        logger.info(f"Registered broker: {broker_name}")
    
    @classmethod
    def create_broker(cls, broker_name: str, client_id: str, access_token: str, 
                     **kwargs) -> Optional[BaseBrokerInterface]:
        """
        Create broker instance
        Args:
            broker_name: Name of broker to create
            client_id: Client/User ID
            access_token: Authentication token
            **kwargs: Additional broker-specific parameters
        Returns:
            Broker instance or None if creation fails
        """
        broker_name = broker_name.lower()
        
        if broker_name not in cls._registered_brokers:
            logger.error(f"Broker '{broker_name}' not registered. Available: {list(cls._registered_brokers.keys())}")
            return None
        
        try:
            broker_class = cls._registered_brokers[broker_name]
            config = cls._broker_configs[broker_name]
            
            # Merge config with kwargs
            broker_kwargs = {**config, **kwargs}
            
            # Create broker instance
            broker = broker_class(client_id, access_token, **broker_kwargs)
            
            logger.info(f"Created {broker_name} broker instance")
            return broker
            
        except Exception as e:
            logger.error(f"Failed to create {broker_name} broker: {str(e)}")
            return None
    
    @classmethod
    def get_available_brokers(cls) -> List[str]:
        """Get list of registered broker names"""
        return list(cls._registered_brokers.keys())
    
    @classmethod
    def load_broker_plugins(cls, plugins_dir: str = "broker_plugins"):
        """
        Dynamically load broker plugins from directory
        Args:
            plugins_dir: Directory containing broker plugin modules
        """
        if not os.path.exists(plugins_dir):
            logger.warning(f"Broker plugins directory not found: {plugins_dir}")
            return
        
        for filename in os.listdir(plugins_dir):
            if filename.endswith('.py') and not filename.startswith('__'):
                module_name = filename[:-3]  # Remove .py extension
                
                try:
                    # Import the module
                    module_path = f"{plugins_dir.replace('/', '.')}.{module_name}"
                    module = importlib.import_module(module_path)
                    
                    # Look for broker class and registration function
                    if hasattr(module, 'register_broker'):
                        module.register_broker(cls)
                        logger.info(f"Loaded broker plugin: {module_name}")
                    else:
                        logger.warning(f"Plugin {module_name} missing register_broker function")
                        
                except Exception as e:
                    logger.error(f"Failed to load broker plugin {module_name}: {str(e)}")
    
    @classmethod
    def auto_discover_brokers(cls):
        """
        Auto-discover and register brokers from broker_plugins directory
        """
        # Load from standard location
        try:
            cls.load_broker_plugins("broker_plugins")
        except Exception as e:
            logger.error(f"Auto-discovery failed: {str(e)}")
    
    @classmethod
    def get_broker_info(cls, broker_name: str) -> Optional[Dict]:
        """
        Get information about a registered broker
        Args:
            broker_name: Name of broker
        Returns:
            Dict with broker info or None
        """
        broker_name = broker_name.lower()
        
        if broker_name not in cls._registered_brokers:
            return None
        
        broker_class = cls._registered_brokers[broker_name]
        config = cls._broker_configs[broker_name]
        
        return {
            'name': broker_name,
            'class': broker_class.__name__,
            'module': broker_class.__module__,
            'config': config,
            'description': broker_class.__doc__ or "No description available"
        }
    
    @classmethod
    def validate_broker_credentials(cls, broker_name: str, client_id: str, 
                                  access_token: str) -> tuple[bool, Optional[str]]:
        """
        Validate broker credentials without creating persistent connection
        Args:
            broker_name: Name of broker
            client_id: Client ID
            access_token: Access token
        Returns:
            (is_valid, error_message)
        """
        broker = cls.create_broker(broker_name, client_id, access_token)
        
        if not broker:
            return False, f"Failed to create {broker_name} broker instance"
        
        try:
            success, error = broker.connect()
            if success:
                broker.disconnect()
                return True, None
            else:
                return False, error
        except Exception as e:
            return False, str(e)

# Global factory instance
broker_factory = BrokerFactory()