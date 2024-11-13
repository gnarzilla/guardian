# src/guardian/services/ssh.py
from pathlib import Path
import subprocess
from typing import Optional
from guardian.core import Service, Result
from rich.console import Console
from rich.prompt import Confirm

console = Console()

class SSHManager(Service):
    """SSH key management service"""
    def __init__(self):
        super().__init__()
        self.ssh_dir = Path.home() / '.ssh'
        self.ssh_dir.mkdir(mode=0o700, exist_ok=True)
    
    def check_existing_keys(self) -> dict:
        """Check for existing SSH keys"""
        keys = {
            'rsa': (self.ssh_dir / 'id_rsa', self.ssh_dir / 'id_rsa.pub'),
            'ed25519': (self.ssh_dir / 'id_ed25519', self.ssh_dir / 'id_ed25519.pub'),
            'ecdsa': (self.ssh_dir / 'id_ecdsa', self.ssh_dir / 'id_ecdsa.pub')
        }
        
        existing = {}
        for key_type, (priv, pub) in keys.items():
            if priv.exists() and pub.exists():
                existing[key_type] = {
                    'private': priv,
                    'public': pub,
                    'permissions': oct(priv.stat().st_mode)[-3:]
                }
        
        return existing

    def generate_key(self, email: str, force: bool = False) -> Result:
        """Generate new SSH key"""
        existing = self.check_existing_keys()
        
        if existing and not force:
            # Show existing keys
            console.print("\n[yellow]Existing SSH keys found:[/yellow]")
            for key_type, info in existing.items():
                console.print(f"• {key_type}: {info['public']}")
            
            if not Confirm.ask("\nDo you want to create a new key anyway?"):
                return self.create_result(
                    False,
                    "Operation cancelled by user"
                )
        
        try:
            key_path = self.ssh_dir / 'id_ed25519'
            
            cmd = [
                'ssh-keygen',
                '-t', 'ed25519',
                '-C', email,
                '-f', str(key_path),
                '-N', ''
            ]
            
            subprocess.run(cmd, check=True)
            key_path.chmod(0o600)
            
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

    def backup_keys(self, backup_dir: Optional[Path] = None) -> Result:
        """Backup existing SSH keys"""
        if backup_dir is None:
            backup_dir = self.config_dir / 'backups' / 'ssh'
        
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            existing = self.check_existing_keys()
            if not existing:
                return self.create_result(
                    False,
                    "No SSH keys found to backup"
                )
            
            import shutil
            for key_type, info in existing.items():
                shutil.copy2(info['private'], backup_dir)
                shutil.copy2(info['public'], backup_dir)
            
            return self.create_result(
                True,
                f"SSH keys backed up to {backup_dir}",
                {'backup_dir': str(backup_dir)}
            )
            
        except Exception as e:
            return self.create_result(
                False,
                "Failed to backup SSH keys",
                error=e
            )
