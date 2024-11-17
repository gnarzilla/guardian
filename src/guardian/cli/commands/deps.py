# src/guardian/cli/commands/deps.py

import click
import subprocess
import toml
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from guardian.services.status import StatusChecker
from guardian.core.auth import AuthService

console = Console()


@click.group()
def deps():
    """Dependencies management commands"""
    pass

@deps.command()
@click.option('--update-toml', is_flag=True, help='Update pyproject.toml')
def sync(update_toml):
    """Sync dependencies with requirements/pyproject.toml"""
    try:
        import pkg_resources
        import toml
        from packaging.requirements import Requirement
        
        # Get installed packages
        installed = {pkg.key: pkg for pkg in pkg_resources.working_set}
        
        # Parse existing pyproject.toml
        with open('pyproject.toml') as f:
            project_data = toml.load(f)
        
        # Organize dependencies
        deps = {}
        dev_deps = {}
        
        for pkg_name, pkg in installed.items():
            if pkg_name == 'guardian':  # Skip our own package
                continue
                
            req = f"{pkg.key}>={pkg.version}"
            
            # Determine if it's a dev dependency
            if pkg_name in ['pytest', 'black', 'mypy', 'isort']:
                dev_deps[pkg_name] = req
            else:
                deps[pkg_name] = req
        
        if update_toml:
            # Update pyproject.toml
            project_data['project']['dependencies'] = list(deps.values())
            project_data['project']['optional-dependencies'] = {
                'dev': list(dev_deps.values())
            }
            
            with open('pyproject.toml', 'w') as f:
                toml.dump(project_data, f)
            
            console.print("[green]✓[/green] Updated pyproject.toml")
        
        # Show current dependencies
        console.print("\n[bold]Dependencies:[/bold]")
        for name, req in deps.items():
            console.print(f"  • {req}")
            
        console.print("\n[bold]Development Dependencies:[/bold]")
        for name, req in dev_deps.items():
            console.print(f"  • {req}")
            
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to sync dependencies: {str(e)}")
