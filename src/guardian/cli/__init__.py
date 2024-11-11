# src/guardian/cli/__init__.py
import click
from rich.console import Console
from rich.table import Table
from guardian.core.auth import AuthService
from guardian.core.config import ConfigService
from guardian.core.repo import RepoService
from guardian.core.security import SecurityService

console = Console()

class Context:
    def __init__(self):
        self.auth = AuthService()
        self.config = ConfigService()
        self.repo = RepoService()
        self.security = SecurityService()

@click.group()
@click.version_option(version="1.0.0", prog_name="Guardian")
@click.pass_context
def cli(ctx):
    """Guardian: Git Authentication & Development Assistant"""
    ctx.obj = Context()
