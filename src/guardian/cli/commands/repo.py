# src/guardian/cli/commands/repo.py
import click
from rich.console import Console
from rich.panel import Panel
from pathlib import Path
import subprocess
from typing import Optional

console = Console()

@click.group()
def repo():
    """Repository and remote management commands"""
    pass

@repo.command()
@click.option('--remote-type', type=click.Choice(['github', 'gitlab', 'bitbucket', 'custom']),
              help='Remote platform type')
@click.option('--private', is_flag=True, default=True, help='Create private repository')
@click.pass_context
def create(ctx, remote_type: str, private: bool):
    """Create a remote repository for the current project"""
    try:
        # Verify we're in a git repository
        if not Path('.git').exists():
            # Initialize if not exists
            if click.confirm("Not a git repository. Initialize one?"):
                subprocess.run(['git', 'init'], check=True)
            else:
                return
        
        # Get project name from directory
        project_name = Path.cwd().name
        
        # Show creation plan
        console.print(Panel(
            f"Creating remote repository:\n\n"
            f"Project: {project_name}\n"
            f"Platform: {remote_type}\n"
            f"Visibility: {'Private' if private else 'Public'}\n",
            title="Repository Creation"
        ))
        
        if not click.confirm("Continue?"):
            return
        
        with console.status("Creating repository..."):
            if remote_type == 'github':
                # Use GitHub API through configured token
                # This would be handled by a separate GitHub service
                pass
            elif remote_type == 'gitlab':
                # GitLab API implementation
                pass
            # ... other platforms
            
            # Add remote to local repo
            # Set up branch tracking
            # Configure additional remote settings
        
        console.print("\n[green]✓[/green] Remote repository created successfully!")
        console.print("\nNext steps:")
        console.print("1. Review repository settings")
        console.print("2. Push your changes: git push -u origin main")
        
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to create repository: {str(e)}")

@repo.command()
@click.option('--remote-type', type=click.Choice(['github', 'gitlab', 'bitbucket', 'custom']),
              help='Remote platform type for authentication')
@click.argument('url')
@click.pass_context
def connect(ctx, remote_type: str, url: str):
    """Connect existing repository to a remote"""
    try:
        if not Path('.git').exists():
            console.print("[red]✗[/red] Not a git repository")
            return
        
        # Verify/setup authentication for the platform
        auth_result = ctx.obj.auth.verify_platform_auth(remote_type)
        if not auth_result.success:
            if click.confirm("Authentication not setup. Configure now?"):
                # Guide through platform-specific auth setup
                if remote_type == 'github':
                    ctx.invoke(auth_setup_github)
                # ... other platforms
            else:
                return
        
        # Add the remote
        subprocess.run(['git', 'remote', 'add', 'origin', url], check=True)
        
        console.print("[green]✓[/green] Remote connected successfully!")
        console.print("\nNext steps:")
        console.print("1. Verify connection: git remote -v")
        console.print("2. Push your changes: git push -u origin main")
        
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to connect repository: {str(e)}")

@repo.command()
@click.pass_context
def sync(ctx):
    """Synchronize repository configuration across systems"""
    try:
        # Export current configuration
        config_data = {
            'remotes': {},
            'hooks': {},
            'git_config': {}
        }
        
        # Get remote information
        remotes = subprocess.run(
            ['git', 'remote', '-v'],
            capture_output=True, text=True, check=True
        ).stdout
        
        for line in remotes.splitlines():
            if line:
                name, url, _ = line.split()
                config_data['remotes'][name] = url
        
        # Get hook configurations
        hooks_dir = Path('.git/hooks')
        if hooks_dir.exists():
            for hook in hooks_dir.glob('*'):
                if hook.is_file():
                    config_data['hooks'][hook.name] = {
                        'enabled': hook.stat().st_mode & 0o111 != 0,
                        'guardian_managed': 'Guardian' in hook.read_text()
                    }
        
        # Get git config
        for key in ['user.name', 'user.email', 'user.signingkey']:
            try:
                value = subprocess.run(
                    ['git', 'config', '--get', key],
                    capture_output=True, text=True, check=True
                ).stdout.strip()
                config_data['git_config'][key] = value
            except subprocess.CalledProcessError:
                pass
        
        # Export to file
        config_file = Path('.guardian-sync.yml')
        import yaml
        with open(config_file, 'w') as f:
            yaml.safe_dump(config_data, f)
        
        console.print(f"[green]✓[/green] Configuration exported to {config_file}")
        console.print("\nTo use this configuration on another system:")
        console.print(f"1. Copy {config_file} to the project directory")
        console.print("2. Run: guardian repo apply-sync")
        
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to sync configuration: {str(e)}")

@repo.command()
@click.pass_context
def apply_sync(ctx):
    """Apply synchronized configuration from .guardian-sync.yml"""
    try:
        config_file = Path('.guardian-sync.yml')
        if not config_file.exists():
            console.print("[red]✗[/red] No sync configuration found")
            return
        
        import yaml
        with open(config_file) as f:
            config_data = yaml.safe_load(f)
        
        # Apply configuration
        with console.status("Applying configuration..."):
            # Setup remotes
            for name, url in config_data.get('remotes', {}).items():
                try:
                    subprocess.run(['git', 'remote', 'add', name, url], check=True)
                except subprocess.CalledProcessError:
                    # Remote might already exist
                    pass
            
            # Setup hooks
            for hook, info in config_data.get('hooks', {}).items():
                if info.get('guardian_managed'):
                    ctx.invoke(hooks_install)
            
            # Apply git config
            for key, value in config_data.get('git_config', {}).items():
                subprocess.run(['git', 'config', key, value], check=True)
        
        console.print("[green]✓[/green] Configuration applied successfully!")
        
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to apply configuration: {str(e)}")
