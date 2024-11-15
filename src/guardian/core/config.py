# src/guardian/core/config.py
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from guardian.core import Service, Result

class ConfigService(Service):
    """Core configuration management service"""
    def __init__(self):
        super().__init__()
        self.config_file = self.config_dir / 'config.yml'
        self._config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        if not self.config_file.exists():
            default_config = {
                'auth': {
                    'ssh_keys': [],
                    'github_tokens': [],
                    'gpg_keys': []
                },
                'git': {
                    'name': None,
                    'email': None,
                    'signing_key': None
                }
            }
            self._save_config(default_config)
            return default_config
            
        try:
            with open(self.config_file) as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            return {}
    
    def _save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to file"""
        self.config_dir.mkdir(exist_ok=True)
        with open(self.config_file, 'w') as f:
            yaml.safe_dump(config, f)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any) -> Result:
        """Set configuration value"""
        try:
            self._config[key] = value
            self._save_config(self._config)
            return self.create_result(True, f"Configuration '{key}' updated")
        except Exception as e:
            return self.create_result(False, f"Failed to update configuration", error=e)
    
    def update_auth_config(self, auth_type: str, name: str, operation: str = 'add') -> Result:
        """Update authentication configuration"""
        try:
            if 'auth' not in self._config:
                self._config['auth'] = {}
            
            key = f"{auth_type}s"  # e.g., 'ssh_keys', 'github_tokens'
            if key not in self._config['auth']:
                self._config['auth'][key] = []
            
            if operation == 'add':
                if name not in self._config['auth'][key]:
                    self._config['auth'][key].append(name)
            elif operation == 'remove':
                if name in self._config['auth'][key]:
                    self._config['auth'][key].remove(name)
            
            self._save_config(self._config)
            return self.create_result(True, f"Updated {auth_type} configuration")
        except Exception as e:
            return self.create_result(
                False, 
                f"Failed to update {auth_type} configuration",
                error=e
            )
