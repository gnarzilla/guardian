# src/guardian/cli/commands/auth.py
@cli.group()
def auth():
    """Authentication management commands"""
    pass

@auth.command()
@click.option('--email', prompt=True, help='Email for SSH key')
@click.option('--force', is_flag=True, help='Overwrite existing key')
@click.pass_context
def setup_ssh(ctx, email, force):
    """Generate and configure SSH keys"""
    result = ctx.obj.auth.setup_ssh(email, force)
    if result.success:
        console.print(f"[green]{result.message}[/green]")
        if result.data:
            console.print(f"Key path: {result.data['key_path']}")
    else:
        console.print(f"[red]Error: {result.message}[/red]")

@auth.command()
@click.option('--token', prompt=True, hide_input=True,
              help='GitHub Personal Access Token')
@click.option('--name', default='default', help='Token name for multiple accounts')
@click.pass_context
def setup_token(ctx, token, name):
    """Store Git authentication token"""
    result = ctx.obj.auth.setup_git_token(token, name)
    if result.success:
        console.print(f"[green]{result.message}[/green]")
    else:
        console.print(f"[red]Error: {result.message}[/red]")
