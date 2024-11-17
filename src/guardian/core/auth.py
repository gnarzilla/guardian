# src/guardian/core/auth.py
from pathlib import Path
from typing import Optional
import logging
from guardian.core import Service, Result
from guardian.core.config import ConfigService
from guardian.services.ssh import SSHManager
from guardian.services.gpg import GPGManager
from guardian.services.keyring import KeyringManager
from guardian.services.api import GitHubAPI
from datetime import datetime, timezone

class AuthService(Service):
    """Core authentication service"""
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.ssh = SSHManager()
        self.gpg = GPGManager()
        self.keyring = KeyringManager()
        self.config = ConfigService() # Initialize ConfigService

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
            self.logger.debug(f"Setting up GitHub token with key: github_token_{name}")
            # Define key outside the try block
            token_key = f"github_token_{name}"
            
            # Validate token with GitHub API before storing
            github = GitHubAPI(token)
            validation = github.validate_token()
            if not validation.valid:
                return self.create_result(
                    False,
                    "Invalid GitHub token",
                    {"error": "Token validation failed"}
                )
            
            # Store in keyring
            store_result = self.keyring.store_credential(token_key, token)
            if not store_result.success:
                return store_result
            
            # Update configuration
            config_result = self.config.update_auth_config('github_token', name)
            if not config_result.success:
                # Rollback keyring storage
                self.keyring.delete_credential(token_key)
                return config_result
            
            return self.create_result(
                True,
                "GitHub token stored successfully"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to store GitHub token: {str(e)}")
            return self.create_result(
                False,
                f"Failed to store GitHub token: {str(e)}",
                error=e
            )

    def validate_github_token(self, name: str = "default") -> Result:
        """Validate GitHub token and check its permissions"""
        try:
            token = self.keyring.get_credential(f"github_token_{name}")
            if not token:
                return self.create_result(
                    False,
                    "No GitHub token found"
                )
            
            # Use GitHub API to validate token
            github = GitHubAPI(token)
            token_info = github.validate_token()
            
            if not token_info.valid:
                return self.create_result(
                    False,
                    "Invalid or expired token"
                )
            
            return self.create_result(
                True,
                "Token validated successfully",
                {
                    'user': token_info.user,
                    'scopes': token_info.scopes,
                    'expires_at': token_info.expires_at.isoformat() if token_info.expires_at else 'Never',
                    'capabilities': token_info.capabilities,
                    'rate_limit': token_info.rate_limit_remaining
                }
            )
            
        except Exception as e:
            self.logger.error(f"Failed to validate GitHub token: {str(e)}")
            return self.create_result(
                False,
                f"Failed to validate GitHub token: {str(e)}",
                error=e
            ) 

    def list_tokens(self) -> Result:
        """List stored GitHub tokens"""
        try:
            # Get auth configuration
            auth_config = self.config.get('auth', {})
            github_tokens = auth_config.get('github_tokens', [])
            
            tokens = []
            for token_name in github_tokens:
                if self.keyring.get_credential(f"github_token_{token_name}"):
                    tokens.append(token_name)
            
            return self.create_result(
                True,
                f"Found {len(tokens)} GitHub tokens",
                {'tokens': tokens}
            )
        except Exception as e:
            self.logger.error(f"Failed to list GitHub tokens: {str(e)}")
            return self.create_result(
                False,
                "Failed to list GitHub tokens",
                error=e
            )

    def list_ssh_keys(self) -> Result:
        """List SSH keys"""
        return self.ssh.list_ssh_keys()
