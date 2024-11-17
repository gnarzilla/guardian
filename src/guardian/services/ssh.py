# src/guardian/services/ssh.py
import subprocess
from pathlib import Path
from typing import List, Dict, Optional
from guardian.core import Service, Result

class SSHManager(Service):
    """SSH key management service"""
    def __init__(self):
        super().__init__()
        self.ssh_dir = Path.home() / '.ssh'
        self.ssh_dir.mkdir(mode=0o700, exist_ok=True)

    def list_ssh_keys(self) -> Result:
        """List all SSH keys with their content"""
        try:
            key_types = {
                'rsa': ('id_rsa', 'id_rsa.pub'),
                'ed25519': ('id_ed25519', 'id_ed25519.pub'),
                'ecdsa': ('id_ecdsa', 'id_ecdsa.pub')
            }

            keys = []
            for key_type, (private, public) in key_types.items():
                pub_path = self.ssh_dir / public
                if pub_path.exists():
                    try:
                        content = pub_path.read_text().strip()
                        keys.append({
                            'type': key_type,
                            'path': str(pub_path),
                            'content': content
                        })
                    except Exception as e:
                        self.logger.warning(f"Could not read key {pub_path}: {e}")

            return self.create_result(
                True,
                f"Found {len(keys)} SSH keys",
                {'keys': keys}
            )
        except Exception as e:
            return self.create_result(
                False,
                "Failed to list SSH keys",
                error=e
            )

    def generate_key(self, email: str, force: bool = False) -> Result:
        """Generate new SSH key"""
        key_path = self.ssh_dir / 'id_ed25519'
        
        if key_path.exists() and not force:
            return self.create_result(
                False,
                f"SSH key already exists at {key_path}. Use --force to overwrite."
            )
        
        try:
            cmd = [
                'ssh-keygen',
                '-t', 'ed25519',
                '-C', email,
                '-f', str(key_path),
                '-N', ''
            ]
            
            subprocess.run(cmd, check=True)
            key_path.chmod(0o600)
            (key_path.parent / f"{key_path.name}.pub").chmod(0o644)
            
            return self.create_result(
                True,
                "SSH key generated successfully",
                {'key_path': str(key_path)}
            )
            
        except subprocess.CalledProcessError as e:
            return self.create_result(
                False,
                "Failed to generate SSH key",
                error=e
            )
