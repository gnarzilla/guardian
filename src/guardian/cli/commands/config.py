# src/guardian/cli/commands/config.py
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
import subprocess

console = Console()

@click.group()
def config():
    """Configuration management commands"""
    pass

@config.command()
@click.argument('key')
@click.argument('value', required=False)
@click.pass_context
def set(ctx, key, value):
    """Set a configuration value"""
    if not value and key in ['user.name', 'user.email', 'user.signingkey']:
        value = click.prompt(f'Enter value for {key}')
    
    try:
        if key.startswith('user.') or key.startswith('commit.'):
            # Git config
            result = subprocess.run(
                ['git', 'config', '--global', key, value],
                check=True,
                capture_output=True,
                text=True
            )
            console.print(f"[green]✓[/green] Git config '{key}' updated")
            
            # Update our config if needed
            if key == 'user.signingkey':
                ctx.obj.config.set('git.signing_key', value)
        else:
            # Guardian config
            result = ctx.obj.config.set(key, value)
            if result.success:
                console.print(f"[green]✓[/green] Config '{key}' updated")
            else:
                console.print(f"[red]✗[/red] Failed to update config: {result.message}")
    except subprocess.CalledProcessError as e:
        console.print(f"[red]✗[/red] Failed to update git config: {e.stderr}")
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {str(e)}")

@config.command()
@click.argument('key', required=False)
@click.pass_context
def get(ctx, key):
    """Get a configuration value"""
    try:
        if not key:
            # Show all config
            git_config = subprocess.run(
                ['git', 'config', '--global', '--list'],
                capture_output=True,
                text=True,
                check=True
            ).stdout.strip()
            
            guardian_config = ctx.obj.config._config
            
            console.print(Panel(
                "\n[bold]Git Configuration:[/bold]\n" +
                "\n".join(f"  {line}" for line in git_config.split('\n')),
                title="Configuration"
            ))
            
            console.print(Panel(
                "\n[bold]Guardian Configuration:[/bold]\n" +
                "\n".join(f"  {k}: {v}" for k, v in guardian_config.items()),
                title="Guardian Settings"
            ))
        else:
            if key.startswith('user.') or key.startswith('commit.'):
                # Git config
                try:
                    value = subprocess.run(
                        ['git', 'config', '--global', key],
                        capture_output=True,
                        text=True,
                        check=True
                    ).stdout.strip()
                    console.print(f"{key} = {value}")
                except subprocess.CalledProcessError:
                    console.print(f"[yellow]No value set for {key}[/yellow]")
            else:
                # Guardian config
                value = ctx.obj.config.get(key)
                if value is not None:
                    console.print(f"{key} = {value}")
                else:
                    console.print(f"[yellow]No value set for {key}[/yellow]")
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {str(e)}")

# src/guardian/cli/commands/config.py (update unset command)

@config.command()
@click.argument('key')
@click.pass_context
def unset(ctx, key):
    """Remove a configuration value"""
    try:
        if key.startswith('user.') or key.startswith('commit.'):
            # Check if value exists first
            try:
                subprocess.run(
                    ['git', 'config', '--global', '--get', key],
                    check=True,
                    capture_output=True
                )
                # Value exists, safe to unset
                subprocess.run(
                    ['git', 'config', '--global', '--unset', key],
                    check=True
                )
                console.print(f"[green]✓[/green] Git config '{key}' removed")
            except subprocess.CalledProcessError:
                console.print(f"[yellow]Note:[/yellow] No value set for '{key}'")
        else:
            # Guardian config
            result = ctx.obj.config.set(key, None)
            if result.success:
                console.print(f"[green]✓[/green] Config '{key}' removed")
            else:
                console.print(f"[red]✗[/red] Failed to remove config: {result.message}")
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {str(e)}")

@config.command()
@click.pass_context
def init(ctx):
    """Initialize configuration with defaults"""
    try:
        # Check git config
        for key in ['user.name', 'user.email']:
            try:
                subprocess.run(
                    ['git', 'config', '--global', key],
                    capture_output=True,
                    check=True
                )
            except subprocess.CalledProcessError:
                value = click.prompt(f'Enter your {key.split(".")[1]}')
                subprocess.run(
                    ['git', 'config', '--global', key, value],
                    check=True
                )
        
        # Initialize guardian config
        result = ctx.obj.config.set('initialized', True)
        if result.success:
            console.print("[green]✓[/green] Configuration initialized")
        else:
            console.print(f"[red]✗[/red] Failed to initialize config: {result.message}")
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {str(e)}")
