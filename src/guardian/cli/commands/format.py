# src/guardian/cli/commands/format.py
import click
from pathlib import Path
from rich.console import Console
from rich.table import Table

console = Console()

@click.group(name='format')
def format_cmd():
    """Code formatting commands"""
    pass

@format_cmd.command()
@click.argument('path', type=click.Path(exists=True), default='.')
@click.option('--check', is_flag=True, help='Check only without making changes')
@click.option('--black/--no-black', default=True, help='Run black formatter')
@click.option('--isort/--no-isort', default=True, help='Run isort formatter')
@click.pass_context
def run(ctx, path, check, black, isort):
    """Format code using configured formatters"""
    formatters = []
    if black:
        formatters.append('black')
    if isort:
        formatters.append('isort')

    if not formatters:
        console.print("[yellow]Warning: No formatters selected[/yellow]")
        return

    with console.status(f"{'Checking' if check else 'Formatting'} code..."):
        result = ctx.obj.format.run(
            Path(path),
            formatters=formatters,
            check_only=check
        )

    if result.success:
        console.print(f"[green]✓ {result.message}[/green]")
        if result.data and 'stats' in result.data:
            table = Table(title="Formatting Results")
            table.add_column("Formatter")
            table.add_column("Files Processed")
            table.add_column("Changes Made")
            
            for formatter, stats in result.data['stats'].items():
                table.add_row(
                    formatter,
                    str(stats['files_processed']),
                    str(stats['changes_made'])
                )
            
            console.print(table)
    else:
        console.print(f"[red]✗ {result.message}[/red]")
        if check:
            raise click.Exit(1)

@format_cmd.command()
@click.pass_context
def configure(ctx):
    """Configure formatting settings"""
    console.print("\n[bold]Formatting Configuration[/bold]")
    
    # Get current config
    config = ctx.obj.config.get('formatting', {})
    
    # Update settings
    config['black_enabled'] = click.confirm(
        "Enable black formatter?",
        default=config.get('black_enabled', True)
    )
    
    config['isort_enabled'] = click.confirm(
        "Enable isort formatter?",
        default=config.get('isort_enabled', True)
    )
    
    # Save config
    result = ctx.obj.config.set('formatting', config)
    if result.success:
        console.print("[green]✓ Configuration updated successfully[/green]")
    else:
        console.print(f"[red]✗ Failed to update configuration: {result.message}[/red]")
