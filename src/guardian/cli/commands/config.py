# src/guardian/cli/commands/config.py
@cli.group()
def config():
    """Configuration management commands"""
    pass

@config.command()
@click.option('--name', prompt=True, help='Git user name')
@click.option('--email', prompt=True, help='Git user email')
@click.option('--signing-key', help='GPG signing key')
@click.pass_context
def setup(ctx, name, email, signing_key):
    """Setup git configuration"""
    result = ctx.obj.config.setup_git_config(name, email, signing_key)
    if result.success:
        console.print(f"[green]{result.message}[/green]")
    else:
        console.print(f"[red]Error: {result.message}[/red]")

