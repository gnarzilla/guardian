# src/guardian/hooks/manager.py
from pathlib import Path
import yaml
from typing import Dict, Any, Optional
from jinja2 import Template

class HookManager:
    def __init__(self):
        self.template_dir = Path(__file__).parent.parent / 'templates' / 'hooks'
        self.template_dir.mkdir(parents=True, exist_ok=True)
    
    def list_templates(self) -> Dict[str, Dict[str, Any]]:
        """List available hook templates"""
        templates = {}
        for file in self.template_dir.glob('*.yml'):
            with open(file) as f:
                templates[file.stem] = yaml.safe_load(f)
        return templates
    
    def generate_hook(self, hook_type: str, template_name: str = 'default',
                     context: Optional[Dict[str, Any]] = None) -> str:
        """Generate hook script from template"""
        template_file = self.template_dir / f'{template_name}.yml'
        if not template_file.exists():
            raise ValueError(f"Template '{template_name}' not found")
        
        with open(template_file) as f:
            template_data = yaml.safe_load(f)
        
        hook_data = template_data['hooks'].get(hook_type)
        if not hook_data:
            raise ValueError(f"No {hook_type} hook in template '{template_name}'")
        
        # Build the script
        script = ["#!/bin/sh", f"# Guardian {hook_type} hook ({template_name} template)"]
        
        # Add guardian check
        script.append("""
# Check if guardian is available
if ! command -v guardian >/dev/null 2>&1; then
    echo "[!] Guardian not found. Please install guardian-git"
    exit 1
fi
""")
        
        # Add each step
        for step in hook_data['steps']:
            script.append(f"\n# {step['name']}")
            if 'command' in step:
                if step.get('fail_on_error', False):
                    script.append(f"{step['command']} || exit 1")
                else:
                    script.append(step['command'])
            if 'script' in step:
                script.append(step['script'])
        
        return '\n'.join(script)

# Update the CLI commands to use templates:
@hooks.command()
@click.option('--template', default='default', help='Hook template to use')
@click.option('--force', is_flag=True, help='Overwrite existing hooks')
@click.pass_context
def install(ctx, template, force):
    """Install Guardian pre-commit hooks"""
    try:
        hook_manager = HookManager()
        
        git_dir = Path('.git')
        if not git_dir.exists():
            console.print("[red]✗[/red] Not a git repository")
            return
        
        # Install pre-commit hook
        hooks_dir = git_dir / 'hooks'
        pre_commit = hooks_dir / 'pre-commit'
        
        if pre_commit.exists() and not force:
            console.print("[yellow]![/yellow] Pre-commit hook already exists")
            if not click.confirm("Overwrite existing hook?"):
                return
        
        # Generate and install the hook
        hook_content = hook_manager.generate_hook('pre-commit', template)
        pre_commit.write_text(hook_content)
        pre_commit.chmod(0o755)
        
        console.print(f"[green]✓[/green] Installed {template} pre-commit hook")
        
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to install hooks: {str(e)}")

@hooks.command()
def templates():
    """List available hook templates"""
    try:
        hook_manager = HookManager()
        templates = hook_manager.list_templates()
        
        console.print("\n[bold]Available Hook Templates:[/bold]")
        for name, data in templates.items():
            console.print(f"\n[cyan]{name}[/cyan]")
            for hook_type, hook_data in data['hooks'].items():
                console.print(f"  • {hook_type}: {hook_data['description']}")
    
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to list templates: {str(e)}")
