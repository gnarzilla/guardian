# src/guardian/utils/tree.py
import click
from rich.tree import Tree
from rich.console import Console
from pathlib import Path
from typing import List, Optional, Union

class CommandTreeGenerator:
    """Generate command trees for CLI documentation"""
    
    def __init__(self, cli: click.Group):
        self.cli = cli
        self.console = Console()
    
    def generate_markdown(self) -> str:
        """Generate markdown representation of command tree"""
        lines = ["# Command Tree\n"]
        self._add_command_to_markdown(self.cli, lines)
        return "\n".join(lines)
    
    def _add_command_to_markdown(self, command: Union[click.Group, click.Command], 
                                lines: List[str], level: int = 0):
        """Recursively build markdown tree"""
        prefix = "    " * level
        if isinstance(command, click.Group):
            lines.append(f"{prefix}* {command.name}/")
            if command.help:
                lines.append(f"{prefix}    - {command.help}")
            
            # Sort commands for consistent output
            sorted_commands = sorted(command.commands.items(), 
                                   key=lambda x: x[0])
            
            for _, cmd in sorted_commands:
                self._add_command_to_markdown(cmd, lines, level + 1)
        else:
            lines.append(f"{prefix}* {command.name}")
            if command.help:
                lines.append(f"{prefix}    - {command.help}")

    def print_tree(self):
        """Print rich tree representation of commands"""
        tree = Tree("guardian", guide_style="bold bright_blue")
        self._add_command_to_tree(self.cli, tree)
        self.console.print(tree)
    
    def _add_command_to_tree(self, command: Union[click.Group, click.Command], 
                            tree: Tree):
        """Recursively build rich tree"""
        if isinstance(command, click.Group):
            for name, cmd in sorted(command.commands.items()):
                branch = tree.add(
                    f"[bold cyan]{name}[/bold cyan]" + 
                    (f"\n[dim]{cmd.help}[/dim]" if cmd.help else "")
                )
                if isinstance(cmd, click.Group):
                    self._add_command_to_tree(cmd, branch)

class ProjectTreeGenerator:
    """Generate tree documentation for project templates"""
    
    def __init__(self, root_path: Path):
        self.root_path = Path(root_path)
        self.console = Console()
        
    def generate_markdown(self, 
                         ignore_patterns: Optional[List[str]] = None) -> str:
        """Generate markdown representation of project tree"""
        if ignore_patterns is None:
            ignore_patterns = ['__pycache__', '*.pyc', '.git', 'venv']
            
        lines = [f"# Project Structure: {self.root_path.name}\n"]
        self._add_path_to_markdown(self.root_path, lines, ignore_patterns)
        return "\n".join(lines)
    
    def _add_path_to_markdown(self, path: Path, lines: List[str], 
                            ignore_patterns: List[str], level: int = 0):
        """Recursively build markdown tree"""
        prefix = "    " * level
        
        # Skip ignored patterns
        if any(path.match(pattern) for pattern in ignore_patterns):
            return
            
        if path.is_dir():
            lines.append(f"{prefix}* {path.name}/")
            
            # Sort entries for consistent output
            entries = sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name))
            
            for entry in entries:
                self._add_path_to_markdown(entry, lines, ignore_patterns, level + 1)
        else:
            lines.append(f"{prefix}* {path.name}")
    
    def print_tree(self, ignore_patterns: Optional[List[str]] = None):
        """Print rich tree representation of project"""
        if ignore_patterns is None:
            ignore_patterns = ['__pycache__', '*.pyc', '.git', 'venv']
            
        tree = Tree(
            f"[bold]{self.root_path.name}[/bold]",
            guide_style="bold bright_blue"
        )
        self._add_path_to_tree(self.root_path, tree, ignore_patterns)
        self.console.print(tree)
    
    def _add_path_to_tree(self, path: Path, tree: Tree, 
                         ignore_patterns: List[str]):
        """Recursively build rich tree"""
        if any(path.match(pattern) for pattern in ignore_patterns):
            return
            
        if path.is_dir():
            branch = tree.add(f"[bold cyan]{path.name}/[/bold cyan]")
            entries = sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name))
            for entry in entries:
                self._add_path_to_tree(entry, branch, ignore_patterns)
        else:
            tree.add(f"[green]{path.name}[/green]")
