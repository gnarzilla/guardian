# src/guardian/core/auth.py
from pathlib import Path
from typing import Optional
from guardian.core import Service, Result
from guardian.services.ssh import SSHManager
from guardian.services.gpg import GPGManager
from guardian.services.keyring import KeyringManager

class AuthService(Service):
    """Core authentication service"""
    def __init__(self):
        super().__init__()
        self.ssh = SSHManager()
        self.gpg = GPGManager()
        self.keyring = KeyringManager()
        
    def setup_ssh(self, email: str, force: bool = False) -> Result:
        """Setup SSH authentication"""
        try:
            key_path = self.ssh.generate_key(email, force)
            return self.create_result(
                success=True,
                message="SSH key generated successfully",
                data={"key_path": str(key_path)}
            )
        except Exception as e:
            return self.create_result(
                success=False,
                message="Failed to generate SSH key",
                error=e
            )
    
    def setup_git_token(self, token: str, name: str = "default") -> Result:
        """Store Git authentication token"""
        try:
            self.keyring.store(f"git_token_{name}", token)
            return self.create_result(
                success=True,
                message="Git token stored successfully"
            )
        except Exception as e:
            return self.create_result(
                success=False,
                message="Failed to store Git token",
                error=e
            )
