# src/guardian/services/key_management.py
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
import subprocess
import json
import shutil
from guardian.core import Service, Result

@dataclass
class KeyHealth:
    """Key health status information"""
    age_days: int
    algorithm: str
    key_size: int
    last_used: Optional[datetime]
    permissions_ok: bool
    recommendations: List[str]

class KeyManager(Service):
    """Advanced key management functionality"""
    
    WEAK_ALGORITHMS = ['rsa1024', 'dsa', 'ecdsa-sha1']
    MAX_KEY_AGE_DAYS = 180  # 6 months
    
    def __init__(self):
        super().__init__()
        self.backup_dir = self.config_dir / 'key_backups'
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.recovery_dir = self.config_dir / 'recovery'
        self.recovery_dir.mkdir(parents=True, exist_ok=True)

    def check_key_health(self, key_path: Path) -> Result:
        """Check health of an SSH key"""
        try:
            if not key_path.exists():
                return self.create_result(
                    False,
                    f"Key not found: {key_path}"
                )
            
            recommendations = []
            
            # Check key age
            age_days = (datetime.now() - datetime.fromtimestamp(key_path.stat().st_mtime)).days
            if age_days > self.MAX_KEY_AGE_DAYS:
                recommendations.append(f"Key is {age_days} days old. Consider rotation.")
            
            # Check algorithm and size
            key_info = self._get_key_info(key_path)
            if key_info['algorithm'] in self.WEAK_ALGORITHMS:
                recommendations.append(f"Using weak algorithm: {key_info['algorithm']}")
            if key_info['algorithm'] == 'rsa' and key_info['size'] < 3072:
                recommendations.append("RSA key size should be at least 3072 bits")
            
            # Check permissions
            permissions = oct(key_path.stat().st_mode)[-3:]
            permissions_ok = permissions == '600' if key_path.name.endswith('.pub') else permissions == '644'
            if not permissions_ok:
                recommendations.append(f"Incorrect permissions: {permissions}")
            
            # Get last used time (if available)
            last_used = self._get_last_used(key_path)
            
            health = KeyHealth(
                age_days=age_days,
                algorithm=key_info['algorithm'],
                key_size=key_info['size'],
                last_used=last_used,
                permissions_ok=permissions_ok,
                recommendations=recommendations
            )
            
            return self.create_result(
                True,
                "Key health check complete",
                {'health': health.__dict__}
            )
            
        except Exception as e:
            return self.create_result(
                False,
                f"Failed to check key health: {str(e)}",
                error=e
            )

    def rotate_keys(self, email: str, backup: bool = True) -> Result:
        """Rotate SSH keys with backup"""
        try:
            # Backup existing keys if requested
            if backup:
                backup_result = self._backup_current_keys()
                if not backup_result.success:
                    return backup_result
            
            # Generate new keys
            from guardian.services.ssh import SSHManager
            ssh = SSHManager()
            result = ssh.generate_key(email, force=True)
            
            if not result.success:
                return result
            
            # Verify new keys
            verify_result = self._verify_new_keys(result.data['key_path'])
            if not verify_result.success:
                # Rollback if verification fails
                if backup:
                    self._restore_from_backup(backup_result.data['backup_path'])
                return verify_result
            
            return self.create_result(
                True,
                "Keys rotated successfully",
                {
                    'new_key': result.data['key_path'],
                    'backup': backup_result.data if backup else None
                }
            )
            
        except Exception as e:
            return self.create_result(
                False,
                f"Failed to rotate keys: {str(e)}",
                error=e
            )

    def create_recovery_bundle(self, password: str) -> Result:
        """Create encrypted recovery bundle"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            bundle_dir = self.recovery_dir / timestamp
            bundle_dir.mkdir(parents=True)
            
            # Collect keys and configs
            self._collect_recovery_items(bundle_dir)
            
            # Create recovery instructions
            self._create_recovery_instructions(bundle_dir)
            
            # Encrypt the bundle
            bundle_file = self.recovery_dir / f"recovery_{timestamp}.tar.gz.gpg"
            self._encrypt_bundle(bundle_dir, bundle_file, password)
            
            # Cleanup
            shutil.rmtree(bundle_dir)
            
            return self.create_result(
                True,
                "Recovery bundle created successfully",
                {'bundle_path': str(bundle_file)}
            )
            
        except Exception as e:
            return self.create_result(
                False,
                f"Failed to create recovery bundle: {str(e)}",
                error=e
            )

    def _get_key_info(self, key_path: Path) -> Dict:
        """Get key algorithm and size"""
        result = subprocess.run(
            ['ssh-keygen', '-l', '-f', str(key_path)],
            capture_output=True,
            text=True
        )
        # Parse output like: "3072 SHA256:... user@host (RSA)"
        parts = result.stdout.split()
        return {
            'size': int(parts[0]),
            'algorithm': parts[-1].strip('()').lower()
        }

    def _get_last_used(self, key_path: Path) -> Optional[datetime]:
        """Get last usage time of key"""
        # This would need integration with system logs
        # For now, return None
        return None

    def _backup_current_keys(self) -> Result:
        """Backup current SSH keys"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = self.backup_dir / timestamp
        backup_path.mkdir(parents=True)
        
        try:
            ssh_dir = Path.home() / '.ssh'
            if not ssh_dir.exists():
                return self.create_result(
                    False,
                    "No SSH directory found"
                )
            
            # Copy all key files
            for file in ssh_dir.glob('id_*'):
                shutil.copy2(file, backup_path)
            
            return self.create_result(
                True,
                "Keys backed up successfully",
                {'backup_path': str(backup_path)}
            )
            
        except Exception as e:
            return self.create_result(
                False,
                f"Failed to backup keys: {str(e)}",
                error=e
            )

    def _verify_new_keys(self, key_path: Path) -> Result:
        """Verify newly generated keys"""
        try:
            # Test key permissions
            if key_path.stat().st_mode & 0o777 != 0o600:
                return self.create_result(
                    False,
                    "Incorrect key permissions"
                )
            
            # Test key validity
            result = subprocess.run(
                ['ssh-keygen', '-l', '-f', str(key_path)],
                capture_output=True
            )
            if result.returncode != 0:
                return self.create_result(
                    False,
                    "Invalid key format"
                )
            
            return self.create_result(True, "Keys verified successfully")
            
        except Exception as e:
            return self.create_result(
                False,
                f"Failed to verify keys: {str(e)}",
                error=e
            )
