# src/guardian/proxy/certs.py
import os
import shutil
from pathlib import Path
import platform
import subprocess
from typing import Optional

class CertificateHelper:
    """Helper for managing proxy certificates"""
    
    def __init__(self, cert_dir: Path):
        self.cert_dir = cert_dir
        self.cert_dir.mkdir(parents=True, exist_ok=True)
    
    def install_system_cert(self) -> bool:
        """Install certificate at system level"""
        system = platform.system().lower()
        
        if system == 'linux':
            return self._install_linux()
        elif system == 'darwin':
            return self._install_macos()
        elif system == 'windows':
            return self._install_windows()
        else:
            raise NotImplementedError(f"System {system} not supported")
    
    def _install_linux(self) -> bool:
        """Install certificate on Linux"""
        try:
            cert_file = self.cert_dir / 'mitmproxy-ca.pem'
            system_cert_dir = Path('/usr/local/share/ca-certificates')
            
            # Copy certificate
            shutil.copy(cert_file, system_cert_dir / 'guardian-proxy.crt')
            
            # Update certificates
            subprocess.run(['sudo', 'update-ca-certificates'], check=True)
            return True
            
        except Exception as e:
            print(f"Failed to install system certificate: {e}")
            return False
    
    def get_browser_instructions(self) -> str:
        """Get browser-specific installation instructions"""
        return """
Certificate Installation Instructions:

Chrome/Chromium:
1. Go to Settings → Privacy and security → Security
2. Click on "Manage certificates"
3. Go to "Authorities" tab
4. Click "Import" and select the certificate file
5. Check "Trust this certificate for identifying websites"

Firefox:
1. Go to Preferences → Privacy & Security
2. Scroll down to Certificates
3. Click "View Certificates"
4. Go to "Authorities" tab
5. Click "Import" and select the certificate file
6. Check "Trust this CA to identify websites"

Certificate Location:
{}
""".format(self.cert_dir / 'mitmproxy-ca.pem')
