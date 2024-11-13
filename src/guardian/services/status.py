# src/guardian/services/status.py
from dataclasses import dataclass
from typing import List, Dict, Optional
from pathlib import Path
import subprocess

@dataclass
class ServiceStatus:
    """Status information for a service"""
    configured: bool
    details: Dict[str, str]
    warnings: List[str]
    recommendations: List[str]

class StatusChecker:
    """Check status of various services and configurations"""
    
    def __init__(self, config_service):
        self.config = config_service

    def check_ssh(self, ssh_dir: Path = Path.home() / '.ssh') -> ServiceStatus:
        """Check SSH configuration status"""
        warnings = []
        recommendations = []
        details = {}
        
        # Check for existing keys
        key_types = {
            'rsa': ('id_rsa', 'id_rsa.pub'),
            'ed25519': ('id_ed25519', 'id_ed25519.pub'),
            'ecdsa': ('id_ecdsa', 'id_ecdsa.pub')
        }
        
        found_keys = []
        for key_type, (private, public) in key_types.items():
            priv_path = ssh_dir / private
            pub_path = ssh_dir / public
            
            if priv_path.exists() and pub_path.exists():
                found_keys.append(key_type)
                try:
                    # Check permissions
                    priv_perms = oct(priv_path.stat().st_mode)[-3:]
                    if priv_perms != '600':
                        warnings.append(f"{private} has incorrect permissions: {priv_perms}")
                        recommendations.append(f"Run: chmod 600 {priv_path}")
                except Exception:
                    warnings.append(f"Could not check permissions for {private}")
        
        details['existing_keys'] = ', '.join(found_keys) if found_keys else 'None'
        
        if not found_keys:
            recommendations.append("Run: guardian auth setup-ssh to create new SSH keys")
        elif 'ed25519' not in found_keys:
            recommendations.append("Consider upgrading to ED25519 keys for better security")
        
        return ServiceStatus(
            configured=bool(found_keys),
            details=details,
            warnings=warnings,
            recommendations=recommendations
        )
    
    def check_git(self) -> ServiceStatus:
        """Check Git configuration status"""
        warnings = []
        recommendations = []
        details = {}
        
        try:
            # Check git config
            configs = {
                'user.name': 'git config --global user.name',
                'user.email': 'git config --global user.email',
                'user.signingkey': 'git config --global user.signingkey'
            }
            
            for key, command in configs.items():
                try:
                    result = subprocess.run(
                        command.split(),
                        capture_output=True,
                        text=True,
                        check=False
                    )
                    value = result.stdout.strip()
                    details[key] = value if value else 'Not set'
                    if not value:
                        recommendations.append(f"Set {key} using: guardian config set {key}")
                except:
                    details[key] = 'Error checking'
                    warnings.append(f"Could not check {key}")
        
        except Exception as e:
            warnings.append(f"Error checking git config: {e}")
        
        return ServiceStatus(
            configured='user.name' in details and 'user.email' in details,
            details=details,
            warnings=warnings,
            recommendations=recommendations
        )

    def check_github(self, keyring_manager) -> ServiceStatus:
        """Check GitHub configuration status"""
        warnings = []
        recommendations = []
        details = {}
        
        # Check configuration
        config = self.config._config.get('auth', {}).get('github_tokens', [])
        
        # Check keyring for each configured token
        tokens_found = []
        for name in config:
            key = f"github_token_{name}"
            if keyring_manager.get_credential(key):
                tokens_found.append(name)
            else:
                warnings.append(f"Token '{name}' configured but not found in keyring")
        
        if tokens_found:
            details['token_status'] = 'Configured'
            details['tokens'] = tokens_found
        else:
            details['token_status'] = 'Not configured'
            recommendations.append("Run: guardian auth setup-github to configure GitHub access")
        
        # Check for gh CLI
        import shutil
        if shutil.which('gh'):
            try:
                result = subprocess.run(
                    ['gh', 'auth', 'status'],
                    capture_output=True,
                    text=True,
                    check=False
                )
                if result.returncode == 0:
                    details['gh_cli'] = 'Authenticated'
                else:
                    details['gh_cli'] = 'Not authenticated'
                    recommendations.append("Run: gh auth login to authenticate GitHub CLI")
            except:
                details['gh_cli'] = 'Error checking'
                warnings.append("Could not check GitHub CLI status")
        else:
            details['gh_cli'] = 'Not installed'
            recommendations.append("Consider installing GitHub CLI: https://cli.github.com")
        
        return ServiceStatus(
            configured=bool(tokens_found),
            details=details,
            warnings=warnings,
            recommendations=recommendations
        )

    def check_gpg(self) -> ServiceStatus:
        """Check GPG configuration status"""
        warnings = []
        recommendations = []
        details = {}
        
        try:
            # Check for gpg command
            if not shutil.which('gpg'):
                details['gpg_status'] = 'Not installed'
                recommendations.append("Install GPG for secure key management")
                return ServiceStatus(
                    configured=False,
                    details=details,
                    warnings=warnings,
                    recommendations=recommendations
                )
            
            # Check for keys
            result = subprocess.run(
                ['gpg', '--list-secret-keys', '--keyid-format', 'LONG'],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                if 'sec' in result.stdout:
                    details['gpg_status'] = 'Keys found'
                    # Parse key details if needed
                    keys = []
                    for line in result.stdout.splitlines():
                        if line.startswith('sec'):
                            key_id = line.split('/')[1].split(' ')[0]
                            keys.append(key_id)
                    details['keys'] = keys
                else:
                    details['gpg_status'] = 'No keys found'
                    recommendations.append("Run: guardian auth setup-gpg to create a GPG key")
            else:
                details['gpg_status'] = 'Error checking'
                warnings.append("Could not check GPG keys")
        
        except Exception as e:
            warnings.append(f"Error checking GPG configuration: {e}")
            details['gpg_status'] = 'Error'
        
        return ServiceStatus(
            configured='keys' in details and details.get('keys', []),
            details=details,
            warnings=warnings,
            recommendations=recommendations
        )
