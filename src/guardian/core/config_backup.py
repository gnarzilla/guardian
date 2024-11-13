# src/guardian/core/config.py
from pathlib import Path
import yaml
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
           self.logger.error(f"Failed to load config:")
           return {}
    def _save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to file"""
        self.config_dir.mkdir(exist_ok=True)
        with open(self.config_file, 'w') as f:
            yaml.safe_dump(self._config, f)
    
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

    def setup_git_config(self, name: str, email: str, 
                        signing_key: Optional[str] = None) -> Result:
        """Setup git configuration"""
        try:
            import subprocess
            cmds = [
                ['git', 'config', '--global', 'user.name', name],
                ['git', 'config', '--global', 'user.email', email]
            ]
            
            if signing_key:
                cmds.extend([
                    ['git', 'config', '--global', 'user.signingkey', signing_key],
                    ['git', 'config', '--global', 'commit.gpgsign', 'true']
                ])
            
            for cmd in cmds:
                subprocess.run(cmd, check=True)
            
            return self.create_result(True, "Git configuration updated successfully")
        except Exception as e:
            return self.create_result(False, "Failed to update git configuration", error=e)

    def update_auth_config(
        self, 
        auth_type: str, 
        name: str,
        operation: str = 'add'
    ) -> Result:
        """Update authenication configuration"""
        try:
            if 'auth' not in self._config:
                self.config['auth'] = {}

            key = f"{auth_type}s"
            if key not in self._config['auth']:
                self._config['auth'][key] = []

            if operation == 'add':
                if name not in self._config['auth'][key]:
                    self.config['auth'][key].remove(name)

            self.save_config(self, config)
            return self.create_result(True, f"Updated {auth_type} configuration")
        except Exception as e:
            return self.create_result(False, f"Failed to update {auth_type} configuration", error=e)
