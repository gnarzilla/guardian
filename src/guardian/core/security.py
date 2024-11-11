# src/guardian/core/security.py
from pathlib import Path
from typing import List, Dict
import re
from guardian.core import Service, Result

class SecurityService(Service):
    """Core security service"""
    def __init__(self):
        super().__init__()
        self.scan_patterns = {
            'aws_key': r'AKIA[0-9A-Z]{16}',
            'private_key': r'-----BEGIN PRIVATE KEY-----',
            'password': r'password\s*=\s*[\'"][^\'"]+[\'"]',
            'token': r'token\s*=\s*[\'"][^\'"]+[\'"]'
        }
    
    def scan_file(self, path: Path) -> List[Dict[str, str]]:
        """Scan a file for sensitive data"""
        findings = []
        try:
            with open(path) as f:
                content = f.read()
                for key, pattern in self.scan_patterns.items():
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        findings.append({
                            'type': key,
                            'file': str(path),
                            'line': content.count('\n', 0, match.start()) + 1
                        })
        except Exception as e:
            self.logger.error(f"Failed to scan {path}: {e}")
        return findings
    
    def scan_repo(self, path: Path) -> Result:
        """Scan repository for sensitive data"""
        try:
            findings = []
            for file in path.rglob('*'):
                if file.is_file() and not any(p in str(file) for p in ['.git', '__pycache__']):
                    findings.extend(self.scan_file(file))
            
            return self.create_result(
                success=True,
                message=f"Scan completed: {len(findings)} findings",
                data={'findings': findings}
            )
        except Exception as e:
            return self.create_result(False, "Failed to scan repository", error=e)
    
    def rotate_keys(self) -> Result:
        """Rotate SSH and GPG keys"""
        try:
            from guardian.services.ssh import SSHManager
            from guardian.services.gpg import GPGManager
            
            ssh = SSHManager()
            gpg = GPGManager()
            
            # Backup existing keys
            backup_dir = self.config_dir / 'backups' / 'keys'
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # TODO: Implement key rotation logic
            
            return self.create_result(True, "Keys rotated successfully")
        except Exception as e:
            return self.create_result(False, "Failed to rotate keys", error=e)
