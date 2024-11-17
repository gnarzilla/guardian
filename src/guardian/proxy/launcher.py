# src/guardian/proxy/launcher.py
import os
import yaml
from pathlib import Path
import asyncio
from mitmproxy.options import Options
from mitmproxy.tools.dump import DumpMaster
from mitmproxy.tools.web.master import WebMaster
from rich.console import Console
from rich.panel import Panel
from pathlib import Path
from .server import GuardianAuthProxy
import logging

console = Console()
logger = logging.getLogger(__name__)

def show_startup_message(host: str, port: int, web: bool = False):
    """Show clean startup message"""
    console.print(Panel(
        "\n".join([
            f"[green]Guardian Proxy Starting[/green]",
            "",
            "[bold]Proxy Configuration:[/bold]",
            f"Host: {host}",
            f"Port: {port}",
            "",
            "[bold]Browser Setup:[/bold]",
            "1. Configure proxy settings:",
            f"   • Host: {host}",
            f"   • Port: {port}",
            "2. Visit any website to test connection",
            "",
            *([
                "[bold]Web Interface:[/bold]",
                f"http://{host}:8081"
            ] if web else [])
        ]),
        title="Guardian Proxy",
        border_style="blue"
    ))


def load_config() -> dict:
    """Load proxy configuration"""
    config_path = Path(__file__).parent / "config" / "default.yml"
    with open(config_path) as f:
        return yaml.safe_load(f)

class ProxyLauncher:
    def __init__(self, config: dict):
        self.config = config
        self.proxy = None
    
    def setup_certificates(self):
        """Setup MITM certificates"""
        cert_path = Path(self.config['proxy']['cert_path']).expanduser()
        cert_path.mkdir(parents=True, exist_ok=True)
        
        if not (cert_path / "mitmproxy-ca.pem").exists():
            logger.info("Generating new certificates...")
            # mitmproxy will generate certs automatically
            
        return str(cert_path)
    
    async def start(self, web_interface: bool = False):
        """Start the proxy server"""
        try:
            opts = Options(
                listen_host=self.config['proxy']['host'],
                listen_port=self.config['proxy']['port'],
                confdir=self.setup_certificates()
            )
            
            # Create master
            master_class = WebMaster if web_interface else DumpMaster
            self.proxy = master_class(opts)
            
            # Add our authentication addon
            guardian = GuardianAuthProxy(self.config)
            self.proxy.addons.add(guardian)
            
            logger.info(f"Starting proxy on {opts.listen_host}:{opts.listen_port}")
            await self.proxy.run()
            
        except Exception as e:
            logger.error(f"Failed to start proxy: {e}")
            raise
    
    async def stop(self):
        """Stop the proxy server"""
        if self.proxy:
            await self.proxy.shutdown()

def main():
    """Main entry point for the proxy"""
    logging.basicConfig(level=logging.INFO)
    
    config = load_config()
    launcher = ProxyLauncher(config)
    
    try:
        asyncio.run(launcher.start())
    except KeyboardInterrupt:
        logger.info("Shutting down proxy...")
        asyncio.run(launcher.stop())
