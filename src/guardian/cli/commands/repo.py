# src/guardian/cli/commands/repo.py
@cli.group()
def repo():
    """Repository management commands"""
    pass

@repo.command()
@click.argument('path', type=click.Path())
@click.option('--template', help='Template name')
@click.pass_context
def init(ctx, path, template):
    """Initialize a new repository"""
    result = ctx.obj.repo.init(Path(path), template)
    if result.success:
        console.print(f"[green]{result.message}[/green]")
    else:
        console.print(f"[red]Error: {result.message}[/red]")

@repo.command()
@click.argument('url')
@click.option('--path', type=click.Path(), help='Clone destination')
@click.option('--branch', help='Branch to clone')
@click.pass_context
def clone(ctx, url, path, branch):
    """Clone a repository"""
    result = ctx.obj.repo.clone(url, Path(path) if path else None, branch)
    if result.success:
        console.print(f"[green]{result.message}[/green]")
    else:
        console.print(f"[red]Error: {result.message}[/red]")
