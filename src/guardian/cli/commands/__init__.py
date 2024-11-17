# src/guardian/cli/commands/__init__.py
"""
Guardian CLI Commands

This module exports all available CLI commands. Add new commands here
after implementing them in their respective modules.
"""
from guardian.cli.commands.auth import auth
from guardian.cli.commands.config import config
from guardian.cli.commands.format import format_cmd
from guardian.cli.commands.hooks import hooks
from guardian.cli.commands.init import init
from guardian.cli.commands.docs import docs  # New!
from guardian.cli.commands.deps import deps  # New!
from guardian.cli.commands.proxy import proxy

__all__ = [
    "auth",
    "config",
    "format_cmd",
    "hooks",
    "init",
    "docs",  # New!
    "deps",
    "proxy"
]

# Note: repo command is imported separately in cli/__init__.py until fully implemented
