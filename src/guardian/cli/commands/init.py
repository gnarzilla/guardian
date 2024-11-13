# src/guardian/cli/commands/init.py
import click
from rich.console import Console
from rich.panel import Panel
from pathlib import Path

console = Console()

@click.command()
@click.option('--path', type=click.Path(), default='.',
              help='Path to initialize Guardian')
@click.pass_context
def init(ctx, path):
    """Initialize Guardian in the current directory"""
    path = Path(path)
    try:
        # Create necessary directories
        guardian_dir = path / '.guardian'
        guardian_dir.mkdir(exist_ok=True)
        
        # Initialize config
        config_result = ctx.obj.config.set('initialized', True)
        if not config_result.success:
            console.print(f"[yellow]Warning: {config_result.message}[/yellow]")
        
        console.print(Panel(
            "\n[green]✓[/green] Guardian initialized successfully\n\n"
            "Next steps:\n"
            "1. Setup SSH authentication:   guardian auth setup-ssh\n"
            "2. Configure GitHub access:    guardian auth setup-github\n"
            "3. Setup commit signing:       guardian auth setup-signing\n"
            "4. Check current status:       guardian auth status",
            title="Guardian Initialization"
        ))
        
    except Exception as e:
        console.print(f"[red]Error initializing Guardian: {str(e)}[/red]")
        raise click.Abort()
