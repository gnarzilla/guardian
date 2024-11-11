# src/guardian/services/gpg.py
from pathlib import Path
import subprocess
from typing import Optional, List
from guardian.core import Service, Result

class GPGManager(Service):
    """GPG key management service"""
    def __init__(self):
        super().__init__()
        self.gpg_dir = Path.home() / '.gnupg'
        self.gpg_dir.mkdir(mode=0o700, exist_ok=True)

    def generate_key(self, name: str, email: str, passphrase: Optional[str] = None) -> Result:
        """Generate a new GPG key pair"""
        try:
            # Create batch configuration
            batch_config = f"""
                %echo Generating GPG key
                Key-Type: RSA
                Key-Length: 4096
                Name-Real: {name}
                Name-Email: {email}
                Expire-Date: 0
                """
            
            if passphrase:
                batch_config += f"Passphrase: {passphrase}\n"
            else:
                batch_config += "%no-protection\n"
                
            batch_config += "%commit\n%echo done\n"
            
            # Write batch configuration to temporary file
            config_path = self.gpg_dir / 'batch'
            config_path.write_text(batch_config)
            config_path.chmod(0o600)
            
            # Generate key
            subprocess.run(
                ['gpg', '--batch', '--gen-key', str(config_path)],
                check=True,
                capture_output=True,
                text=True
            )
            
            # Clean up
            config_path.unlink()
            
            # Get the key ID
            result = subprocess.run(
                ['gpg', '--list-secret-keys', '--keyid-format', 'LONG', email],
                check=True,
                capture_output=True,
                text=True
            )
            
            # Extract key ID from output
            key_id = None
            for line in result.stdout.splitlines():
                if line.startswith('sec'):
                    key_id = line.split('/')[1].split(' ')[0]
                    break
            
            return self.create_result(
                True,
                "GPG key generated successfully",
                {'key_id': key_id}
            )
            
        except subprocess.CalledProcessError as e:
            return self.create_result(
                False,
                "Failed to generate GPG key",
                error=e
            )
            
    def list_keys(self) -> List[dict]:
        """List all GPG keys"""
        try:
            result = subprocess.run(
                ['gpg', '--list-secret-keys', '--keyid-format', 'LONG'],
                check=True,
                capture_output=True,
                text=True
            )
            
            keys = []
            current_key = {}
            
            for line in result.stdout.splitlines():
                if line.startswith('sec'):
                    if current_key:
                        keys.append(current_key)
                    current_key = {'type': 'sec'}
                    key_parts = line.split('/')
                    if len(key_parts) > 1:
                        current_key['key_id'] = key_parts[1].split(' ')[0]
                elif line.startswith('uid'):
                    uid_parts = line.split('] ')[1].split(' <')
                    current_key['name'] = uid_parts[0]
                    current_key['email'] = uid_parts[1].rstrip('>')
            
            if current_key:
                keys.append(current_key)
                
            return keys
            
        except subprocess.CalledProcessError:
            return []

    def export_public_key(self, key_id: str) -> Optional[str]:
        """Export public key"""
        try:
            result = subprocess.run(
                ['gpg', '--armor', '--export', key_id],
                check=True,
                capture_output=True,
                text=True
            )
            return result.stdout
        except subprocess.CalledProcessError:
            return None

    def delete_key(self, key_id: str, secret: bool = True) -> Result:
        """Delete a GPG key"""
        try:
            if secret:
                subprocess.run(
                    ['gpg', '--delete-secret-key', key_id],
                    check=True,
                    input=b'y\ny\n'
                )
            subprocess.run(
                ['gpg', '--delete-key', key_id],
                check=True,
                input=b'y\n'
            )
            return self.create_result(True, "GPG key deleted successfully")
        except subprocess.CalledProcessError as e:
            return self.create_result(
                False,
                "Failed to delete GPG key",
                error=e
            )
