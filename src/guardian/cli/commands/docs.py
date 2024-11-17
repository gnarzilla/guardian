# src/guardian/cli/commands/docs.py
import click
from rich.console import Console
from rich.markdown import Markdown
from rich.tree import Tree
from pathlib import Path
from guardian.utils.tree import CommandTreeGenerator, ProjectTreeGenerator

console = Console()

@click.group()
def docs():
    """Documentation management commands"""
    pass

@docs.command()
@click.option('--format', type=click.Choice(['markdown', 'tree']), 
              default='tree', help='Output format')
@click.option('--output', type=click.Path(), help='Output file for markdown')
@click.pass_context
def commands(ctx, format, output):
    """Generate command tree documentation"""
    generator = CommandTreeGenerator(ctx.obj.cli)
    
    if format == 'tree':
        generator.print_tree()
    else:
        content = generator.generate_markdown()
        if output:
            Path(output).write_text(content)
            console.print(f"[green]✓[/green] Command tree written to {output}")
        else:
            console.print(Markdown(content))

@docs.command()
@click.argument('path', type=click.Path(exists=True), default='.')
@click.option('--format', type=click.Choice(['markdown', 'tree']), 
              default='tree', help='Output format')
@click.option('--output', type=click.Path(), help='Output file for markdown')
@click.option('--ignore', multiple=True, help='Patterns to ignore')
def project(path, format, output, ignore):
    """Generate project structure documentation"""
    generator = ProjectTreeGenerator(Path(path))
    ignore_patterns = list(ignore) if ignore else None
    
    if format == 'tree':
        generator.print_tree(ignore_patterns)
    else:
        content = generator.generate_markdown(ignore_patterns)
        if output:
            Path(output).write_text(content)
            console.print(f"[green]✓[/green] Project tree written to {output}")
        else:
            console.print(Markdown(content))
