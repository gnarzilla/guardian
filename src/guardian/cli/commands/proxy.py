# src/guardian/cli/commands/proxy.py
import click
from rich.console import Console
from guardian.proxy.launcher import ProxyLauncher, load_config
from guardian.proxy.certs import CertificateHelper
from pathlib import Path

console = Console()

@click.group()
def proxy():
    """Proxy server management"""
    pass

@proxy.command()
@click.option('--web/--no-web', default=False, help='Start with web interface')
@click.option('--setup-cert', is_flag=True, help='Setup certificates before starting')
@click.pass_context
def start(ctx, web, setup_cert):
    """Start the authentication proxy"""
    try:
        config = load_config()
        cert_dir = Path(config['proxy']['cert_path']).expanduser()
        
        if setup_cert:
            helper = CertificateHelper(cert_dir)
            console.print(helper.get_browser_instructions())
            if click.confirm("Would you like to install system certificate?"):
                if helper.install_system_cert():
                    console.print("[green]✓[/green] System certificate installed")
                else:
                    console.print("[yellow]![/yellow] Failed to install system certificate")
                    if not click.confirm("Continue anyway?"):
                        return
        
        launcher = ProxyLauncher(config)
        
        console.print(f"\nStarting Guardian proxy...")
        console.print(f"Configure your browser/system to use proxy: "
                     f"{config['proxy']['host']}:{config['proxy']['port']}")
        
        if web:
            console.print(f"Web interface available at: "
                         f"http://{config['proxy']['host']}:8081")
        
        # Start the proxy
        import asyncio
        asyncio.run(launcher.start(web_interface=web))
        
    except Exception as e:
        console.print(f"[red]Failed to start proxy: {str(e)}[/red]")

@proxy.command()
def cert():
    """Show certificate installation instructions"""
    try:
        config = load_config()
        cert_dir = Path(config['proxy']['cert_path']).expanduser()
        helper = CertificateHelper(cert_dir)
        console.print(helper.get_browser_instructions())
        
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
