# src/guardian/cli/__init__.py
"""
Guardian CLI Entry Point
This module initializes the Guardian CLI application and registers all available
commands. It provides the main CLI group and context management.
"""
import click
from rich.console import Console
from guardian.core.auth import AuthService
from guardian.core.config import ConfigService
from guardian.core.repo import RepoService
from guardian.core.security import SecurityService

# Initialize Rich console for prettier output
console = Console()

class Context:
    """
    CLI Context Class
    
    Holds instances of all core services that commands might need.
    Passed to all commands via Click's context object.
    """
    def __init__(self):
        self.auth = AuthService()
        self.config = ConfigService()
        self.repo = RepoService()
        self.security = SecurityService()
        self.cli = cli

@click.group()
@click.version_option(
    version="1.0.0",
    prog_name="Guardian",
    message="%(prog)s version %(version)s",
)
@click.pass_context
def cli(ctx):
    """Guardian: Git Authentication & Development Assistant"""
    ctx.obj = Context()

# Import all command groups
from guardian.cli.commands import (
    auth,
    config,
    format_cmd,
    hooks,
    init,
    docs,
    deps,
    proxy
)
from guardian.cli.commands.repo import repo  # Import repo separately

# Define available commands with descriptions
COMMANDS = [
    (auth, "Authentication management"),
    (config, "Configuration management"),
    (hooks, "Git hooks management"),
    (format_cmd, "Code formatting"),
    (init, "Initialize Guardian"),
    (docs, "Documentation generation"),
    (deps, "Dependencies management"),
    (proxy, "Proxy server management")
]

# Register core commands
for command, description in COMMANDS:
    if not getattr(command, 'help', None) and description:
        command.help = description
    cli.add_command(command)

# Register repo command separately
cli.add_command(repo)

if __name__ == "__main__":
    cli()
