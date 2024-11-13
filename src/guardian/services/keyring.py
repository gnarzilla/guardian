# src/guardian/services/keyring.py
import keyring
import logging
from typing import Optional
from guardian.core import Service, Result

class KeyringManager(Service):
    """Secure credential storage using system keyring"""
    
    def __init__(self, service_name: str = "guardian"):
        """
        Initialize KeyringManager
        
        Args:
            service_name: Name to use for keyring service
        """
        super().__init__()
        self.service_name = service_name
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.DEBUG)

    def store_credential(self, key: str, value: str) -> Result:
        """Store a credential in the system keyring"""
        try:
            self.logger.debug(f"Attempting to store credential with key: {key}")
            keyring.set_password(self.service_name, key, value)

            # Verify storage
            stored = self.get_credential(key)
            if stored == value:
                self.logger.debug("Credential stored and verified successfully")
                return self.create_result(
                    True,
                    f"Credential '{key}' stored successfully"
                )
            else:  # Fixed indentation and spelling
                self.logger.error("Credential verification failed - stored value doesn't match")
                return self.create_result(
                    False,
                    "Credential verification failed"
                )
        except Exception as e:
            self.logger.error(f"Failed to store credential: {str(e)}")  # Fixed typo in 'store'
            return self.create_result(
                False,
                f"Failed to store credential '{key}'",
                error=e
            )

    def get_credential(self, key: str) -> Optional[str]:
        """Retrieve a credential from the system keyring"""
        try:
            self.logger.debug(f"Attempting to retrieve credential with key: {key}")
            value = keyring.get_password(self.service_name, key)  # Store result in value
            self.logger.debug(f"Credential retrieval result: {'Found' if value else 'Not found'}")
            return value  # Return the value
        except Exception as e:
            self.logger.error(f"Failed to retrieve credential '{key}': {e}")
            return None

    def list_credentials(self) -> Result:
        """List all stored credential keys"""
        try:
            self.logger.debug("Listing credentials")
            keys = []
            known_prefixes = ['github_token_', 'gpg_key_', 'ssh_key_']
            for prefix in known_prefixes:  # Fixed variable name from 'key' to 'prefix'
                if self.get_credential(f"{prefix}default"):
                    keys.append(f"{prefix}default")
            
            return self.create_result(  # Added missing return statement
                True,
                f"Found {len(keys)} credentials",
                {'keys': keys}
            )
        except Exception as e:
            self.logger.error(f"Failed to list credentials: {e}")
            return self.create_result(
                False,
                "Failed to list credentials",
                error=e
            )

    # ... rest of the methods remain the same ...
    def delete_credential(self, key: str) -> Result:
        """
        Delete a credential from the system keyring
        
        Args:
            key: Identifier for the credential to delete
            
        Returns:
            Result indicating success or failure
        """
        try:
            if self.get_credential(key):
                keyring.delete_password(self.service_name, key)
                return self.create_result(
                    True,
                    f"Credential '{key}' deleted successfully"
                )
            return self.create_result(
                False,
                f"Credential '{key}' not found"
            )
        except Exception as e:
            return self.create_result(
                False,
                f"Failed to delete credential '{key}'",
                error=e
            )
    def rotate_credential(self, key: str, new_value: str) -> Result:
        """
        Safely rotate a credential value
        
        Args:
            key: Identifier for the credential
            new_value: New value to store
            
        Returns:
            Result indicating success or failure
        """
        try:
            # Keep old value in case we need to rollback
            old_value = self.get_credential(key)
            if old_value is None:
                return self.create_result(
                    False,
                    f"Credential '{key}' not found"
                )
            
            # Try to store new value
            store_result = self.store_credential(key, new_value)
            if not store_result.success:
                return store_result
            
            return self.create_result(
                True,
                f"Credential '{key}' rotated successfully"
            )
        except Exception as e:
            # Try to rollback if we have the old value
            if old_value:
                try:
                    self.store_credential(key, old_value)
                except Exception:
                    pass
            
            return self.create_result(
                False,
                f"Failed to rotate credential '{key}'",
                error=e
            )
