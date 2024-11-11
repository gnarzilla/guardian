# src/guardian/services/ssh.py
from pathlib import Path
import subprocess
from typing import Optional
from guardian.core import Service, Result

class SSHManager(Service):
    """SSH key management service"""
    def __init__(self):
        super().__init__()
        self.ssh_dir = Path.home() / '.ssh'
        self.ssh_dir.mkdir(mode=0o700, exist_ok=True)
    
    def generate_key(self, email: str, force: bool = False) -> Path:
        """Generate new SSH key"""
        key_path = self.ssh_dir / 'id_ed25519'
        
        if key_path.exists() and not force:
            raise FileExistsError("SSH key already exists")
        
        cmd = [
            'ssh-keygen',
            '-t', 'ed25519',
            '-C', email,
            '-f', str(key_path),
            '-N', ''
        ]
        
        subprocess.run(cmd, check=True)
        key_path.chmod(0o600)
        return key_path
