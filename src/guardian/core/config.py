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
        self._config: Dict[str, Any] = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        if not self.config_file.exists():
            return {}
        try:
            with open(self.config_file) as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            return {}
    
    def _save_config(self) -> None:
        """Save configuration to file"""
        with open(self.config_file, 'w') as f:
            yaml.safe_dump(self._config, f)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any) -> Result:
        """Set configuration value"""
        try:
            self._config[key] = value
            self._save_config()
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
