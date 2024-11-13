# src/guardian/cli/commands/hooks.py
import click
from rich.console import Console
from rich.panel import Panel
from pathlib import Path
import subprocess
import shutil
import yaml
from typing import Optional
from guardian.utils.export import ExportManager

console = Console()

@click.group()
def hooks():
    """Pre-commit hook management"""
    pass

@hooks.command()
def templates():
    """List available hook templates"""
    # Get the directory where the hooks.py file is located
    current_dir = Path(__file__).parent
    
    # Navigate to the guardian root directory and then to templates/hooks
    template_dir = current_dir.parent.parent / 'templates' / 'hooks'
    
    # Debug output to help verify paths
    console.print(f"Looking for templates in: {template_dir}")
    
    if not template_dir.exists():
        console.print("[red]No templates directory found[/red]")
        return
    
    templates_found = False
    console.print("\n[bold]Available Hook Templates:[/bold]")
    
    # Look specifically for YAML files
    for template_file in template_dir.glob('*.yml'):
        try:
            with open(template_file) as f:
                data = yaml.safe_load(f)
                templates_found = True
                console.print(f"\n[cyan]{template_file.stem}[/cyan]")
                for hook_type, hook_data in data['hooks'].items():
                    desc = hook_data.get('description', 'No description available')
                    console.print(f"  • {hook_type}: {desc}")
        except Exception as e:
            console.print(f"[red]Error loading {template_file.name}: {str(e)}[/red]")
    
    if not templates_found:
        console.print("\n[yellow]Template directory structure:[/yellow]")
        try:
            for item in template_dir.iterdir():
                console.print(f"  • {item.name}")
        except Exception as e:
            console.print(f"[red]Error listing directory: {str(e)}[/red]") 

@hooks.command()
@click.option(
    '--template', 
    type=click.Choice(['default', 'strict'], case_sensitive=False),
    default='default',
    help='Hook template to use'
)
@click.option(
    '--force', 
    is_flag=True, 
    help='Overwrite existing hooks'
)
@click.option(
    '--export', 
    type=click.Choice(['json', 'yaml', 'csv', 'xml']),
    help='Export hook configuration'
)
@click.option(
    '--output-dir',
    type=click.Path(),
    help='Directory for exported files'
)
@click.pass_context
def install(ctx, template: str, force: bool, export: str = None, output_dir: str = None):
    """Install Git hooks using specified template"""
    try:
        # Get template directory
        current_dir = Path(__file__).parent
        template_dir = current_dir.parent.parent / 'templates' / 'hooks'
        template_file = template_dir / f'{template}.yml'
        
        if not template_file.exists():
            console.print(f"[red]✗[/red] Template '{template}' not found at {template_file}")
            available = [f.stem for f in template_dir.glob('*.yml')]
            if available:
                console.print("\nAvailable templates:")
                for temp in available:
                    console.print(f"  • {temp}")
            return
        
        # Load template configuration
        with open(template_file) as f:
            hook_config = yaml.safe_load(f)
        
        # Export if requested
        if export:
            try:
                exported = ExportManager.export(
                    hook_config,
                    format=export,
                    output_dir=Path(output_dir) if output_dir else None
                )
                if output_dir:
                    console.print(f"[green]✓[/green] Configuration exported to {output_dir}")
                else:
                    console.print("\n[bold]Hook Configuration:[/bold]")
                    console.print(exported)
            except Exception as e:
                console.print(f"[red]✗[/red] Export failed: {str(e)}")
        
        # Check for git repository
        git_dir = Path('.git')
        if not git_dir.exists():
            console.print("[red]✗[/red] Not a git repository")
            console.print("Run 'git init' first to initialize a repository")
            return

        # Setup hooks directory and files
        hooks_dir = git_dir / 'hooks'
        pre_commit = hooks_dir / 'pre-commit'
        
        if pre_commit.exists() and not force:
            console.print("[yellow]![/yellow] Pre-commit hook already exists")
            if not click.confirm("Overwrite existing hook?"):
                return
        
        # Generate hook script
        if 'pre-commit' not in hook_config.get('hooks', {}):
            console.print(f"[red]✗[/red] No pre-commit configuration found in {template} template")
            return
            
        hook_content = generate_hook_script(hook_config['hooks']['pre-commit'])
        
        # Write hook file
        pre_commit.write_text(hook_content)
        pre_commit.chmod(0o755)
        
        console.print(f"[green]✓[/green] Successfully installed {template} pre-commit hook")
        console.print("\nTest your hook with:")
        console.print("  git commit -m 'test commit'")
        
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to install hooks: {str(e)}")
        console.print("\nFor more details, run with --debug flag")

def generate_hook_script(hook_config: dict) -> str:
    """Generate hook script from configuration"""
    script = [
        "#!/bin/sh",
        "# Guardian pre-commit hook",
        "",
        "# Check if guardian is available",
        'if ! command -v guardian >/dev/null 2>&1; then',
        '    echo "[!] Guardian not found. Please install guardian-git"',
        '    exit 1',
        'fi',
        ""
    ]
    
    # Add steps from template
    for step in hook_config.get('steps', []):
        script.append(f"# {step['name']}")
        if 'command' in step:
            if step.get('fail_on_error', False):
                script.append(f"{step['command']} || exit 1")
            else:
                script.append(step['command'])
        if 'script' in step:
            script.append(step['script'])
        script.append("")
    
    return '\n'.join(script)

@hooks.command()
def list():
    """List installed hooks and their status"""
    try:
        git_dir = Path('.git')
        if not git_dir.exists():
            console.print("[red]✗[/red] Not a git repository")
            return

        hooks_dir = git_dir / 'hooks'
        available_hooks = {
            'pre-commit': 'Runs before creating a commit',
            'pre-push': 'Runs before pushing commits',
            'commit-msg': 'Validates commit messages',
        }

        console.print("\n[bold]Hook Status:[/bold]")
        for hook, description in available_hooks.items():
            hook_path = hooks_dir / hook
            if hook_path.exists():
                is_guardian = 'Guardian' in hook_path.read_text()
                status = "[green]Active (Guardian)[/green]" if is_guardian else "[yellow]Active (Custom)[/yellow]"
            else:
                status = "[dim]Not installed[/dim]"
            console.print(f"  • {hook}: {status}")
            console.print(f"    {description}")

    except Exception as e:
        console.print(f"[red]✗[/red] Failed to list hooks: {str(e)}")

@hooks.command()
@click.argument('hook_type', type=click.Choice(['pre-commit', 'pre-push', 'commit-msg']))
def show(hook_type):
    """Show content of an installed hook"""
    try:
        git_dir = Path('.git')
        if not git_dir.exists():
            console.print("[red]✗[/red] Not a git repository")
            return

        hook_path = git_dir / 'hooks' / hook_type
        if not hook_path.exists():
            console.print(f"[yellow]![/yellow] No {hook_type} hook installed")
            return

        console.print(Panel(
            hook_path.read_text(),
            title=f"{hook_type} Hook Content",
            expand=False
        ))

    except Exception as e:
        console.print(f"[red]✗[/red] Failed to show hook: {str(e)}")

@hooks.command()
@click.argument('hook_type', type=click.Choice(['pre-commit', 'pre-push', 'commit-msg']))
def remove(hook_type):
    """Remove an installed hook"""
    try:
        git_dir = Path('.git')
        if not git_dir.exists():
            console.print("[red]✗[/red] Not a git repository")
            return

        hook_path = git_dir / 'hooks' / hook_type
        if not hook_path.exists():
            console.print(f"[yellow]![/yellow] No {hook_type} hook installed")
            return

        if click.confirm(f"Remove {hook_type} hook?"):
            hook_path.unlink()
            console.print(f"[green]✓[/green] {hook_type} hook removed")

    except Exception as e:
        console.print(f"[red]✗[/red] Failed to remove hook: {str(e)}")
