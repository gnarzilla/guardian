# src/guardian/cli/commands/auth.py
import click
import subprocess
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from guardian.services.status import StatusChecker
from guardian.core.auth import AuthService

console = Console()

@click.group()
def auth():
    """Authentication management commands"""
    pass

@auth.command()
@click.option('--token', help='GitHub Personal Access Token')
@click.option('--name', default='default', help='Name for multiple accounts')
@click.pass_context
def setup_github(ctx, token, name):
    """Configure GitHub Personal Access Token (PAT) for authentication"""
    if not token:
        console.print(Panel(
            Markdown("""
            # Creating a GitHub Personal Access Token (PAT)

            1. Visit [GitHub Token Settings](https://github.com/settings/tokens)
            2. Click "Generate new token (classic)"
            3. Set a note (e.g., "Guardian CLI")
            4. Select scopes:
               - `repo` (Full control of repositories)
               - `read:org` (Read org membership)
               - `admin:public_key` (Manage public keys)
            5. Click "Generate token"
            6. Copy the generated token (you won't see it again!)
            
            [Create new token now →](https://github.com/settings/tokens/new)
            """),
            title="GitHub Token Instructions",
            expand=False
        ))
        
        token = click.prompt(
            'Enter your GitHub Personal Access Token',
            hide_input=True,
            confirmation_prompt=True
        )
    
    service = AuthService()  # Create service instance
    result = service.setup_git_token(token, name)
    
    if result.success:
        console.print(f"[green]✓ {result.message}[/green]")
        console.print("\nToken stored securely. You can now:")
        console.print("  • Clone private repositories")
        console.print("  • Push to repositories")
        console.print("  • Manage SSH keys")
    else:
        console.print(f"[red]✗ {result.message}[/red]")

@auth.command()
@click.option('--email', prompt=True, help='Email for SSH key')
@click.option('--force', is_flag=True, help='Overwrite existing key if it exists')
@click.pass_context
def setup_ssh(ctx, email, force):
    """Generate and configure SSH keys"""
    if not force:
        console.print(Panel(
            "[yellow]Note: Use --force to overwrite existing keys[/yellow]",
            title="SSH Key Generation"
        ))
    
    result = ctx.obj.auth.setup_ssh(email, force)
    if result.success:
        console.print(f"[green]✓ {result.message}[/green]")
        if result.data and 'key_path' in result.data:
            pub_key_path = f"{result.data['key_path']}.pub"
            console.print(f"\nPublic key path: {pub_key_path}")
            try:
                with open(pub_key_path) as f:
                    key_content = f.read().strip()
                console.print("\nPublic key (ready to copy):")
                console.print(Panel(key_content, expand=False))
            except Exception as e:
                console.print(f"[yellow]Could not read public key: {e}[/yellow]")
    else:
        console.print(f"[red]✗ {result.message}[/red]")
        if not force:
            console.print("\nTip: Use --force to overwrite existing keys:")
            console.print("  guardian auth setup-ssh --email your@email.com --force")

@auth.command()
@click.pass_context
def status(ctx):
    """Check status of all authentication methods"""
    checker = StatusChecker(ctx.obj.config)  # Pass config service
    
    # Check SSH
    ssh_status = checker.check_ssh()
    console.print(Panel(
        "\n".join([
            "[bold]SSH Keys:[/bold]",
            f"Status: {'[green]Configured[/green]' if ssh_status.configured else '[yellow]Not Configured[/yellow]'}",
            f"Existing Keys: {ssh_status.details['existing_keys']}",
            *(
                ["\n[yellow]Warnings:[/yellow]"] + 
                [f"• {w}" for w in ssh_status.warnings] 
                if ssh_status.warnings else []
            ),
            *(
                ["\n[blue]Recommendations:[/blue]"] + 
                [f"• {r}" for r in ssh_status.recommendations] 
                if ssh_status.recommendations else []
            )
        ]),
        title="SSH Configuration",
        expand=False
    ))
    
    # Check Git
    git_status = checker.check_git()
    console.print(Panel(
        "\n".join([
            "[bold]Git Configuration:[/bold]",
            f"User Name: {git_status.details.get('user.name', 'Not set')}",
            f"Email: {git_status.details.get('user.email', 'Not set')}",
            f"Signing Key: {git_status.details.get('user.signingkey', 'Not set')}",
            *(
                ["\n[yellow]Warnings:[/yellow]"] + 
                [f"• {w}" for w in git_status.warnings] 
                if git_status.warnings else []
            ),
            *(
                ["\n[blue]Recommendations:[/blue]"] + 
                [f"• {r}" for r in git_status.recommendations] 
                if git_status.recommendations else []
            )
        ]),
        title="Git Configuration",
        expand=False
    ))
    
    # Check GitHub
    github_status = checker.check_github(ctx.obj.auth.keyring)
    console.print(Panel(
        "\n".join([
            "[bold]GitHub Configuration:[/bold]",
            f"Token: {github_status.details['token_status']}",
            f"GitHub CLI: {github_status.details['gh_cli']}",
            *(
                ["\n[yellow]Warnings:[/yellow]"] + 
                [f"• {w}" for w in github_status.warnings] 
                if github_status.warnings else []
            ),
            *(
                ["\n[blue]Recommendations:[/blue]"] + 
                [f"• {r}" for r in github_status.recommendations] 
                if github_status.recommendations else []
            )
        ]),
        title="GitHub Configuration",
        expand=False
    ))

@auth.command()
@click.pass_context
def validate_github(ctx):
    """Validate GitHub token and show its capabilities"""
    result = ctx.obj.auth.validate_github_token()
    if result.success and result.data:
        # Format scopes in columns
        scopes = result.data.get('scopes', [])
        scope_lines = []
        current_line = []
        current_length = 0
        for scope in scopes:
            if current_length + len(scope) > 60:  # Max line length
                scope_lines.append(" ".join(current_line))
                current_line = []
                current_length = 0
            current_line.append(f"[green]✓[/green] {scope}")
            current_length += len(scope) + 2
        if current_line:
            scope_lines.append(" ".join(current_line))

        # Format capabilities as bullet points
        capabilities = result.data.get('capabilities', [])
        capability_lines = [f"  • {cap}" for cap in capabilities]

        console.print(Panel(
            "\n".join([
                "[bold]Token Information[/bold]",
                f"User: {result.data['user']}",
                f"Expires: {result.data.get('expires_at', '[green]Never expires[/green]')}",
                f"Rate Limit Remaining: {result.data.get('rate_limit', 'Unknown')}",
                "",
                "[bold]Scopes:[/bold]",
                *scope_lines,
                "",
                "[bold]Capabilities:[/bold]",
                *capability_lines
            ]),
            title="GitHub Token Status",
            expand=False,
            padding=(1, 2)  # Add some padding for better readability
        ))
    else:
        console.print(f"[red]✗ {result.message}[/red]")
        console.print("\nTo set up a new token:")
        console.print("1. Run: guardian auth setup-github")
        console.print("2. Visit: https://github.com/settings/tokens")

@auth.command()
@click.pass_context
def list(ctx):
    """List configured authentication methods"""
    # Check SSH keys
    ssh_result = ctx.obj.auth.list_ssh_keys()
    if ssh_result.success and ssh_result.data.get('keys'):
        console.print("\n[bold]SSH Keys:[/bold]")
        for key in ssh_result.data['keys']:
            console.print(f"  • {key}")
    else:
        console.print("\n[dim]No SSH keys found[/dim]")

    # Check GitHub tokens
    token_result = ctx.obj.auth.list_tokens()
    if token_result.success and token_result.data.get('tokens'):
        console.print("\n[bold]GitHub Tokens:[/bold]")
        for name in token_result.data['tokens']:
            console.print(f"  • {name}")
    else:
        console.print("\n[dim]No GitHub tokens configured[/dim]")

@auth.command()
@click.pass_context
def debug_tokens(ctx):
    """Debug token storage (development only)"""
    console.print("\n[bold yellow]Token Storage Debug:[/bold yellow]")

    # Show configuration
    config = ctx.obj.config._config.get('auth',{})
    console.print("\n[bold]Configured tokens:[/bold]")
    for token in config.get('github_tokens', []):
        key = f"github_token_{token}"
        value = ctx.obj.auth.keyring.get_credential(key)
        console.print(f"  • {token}: {'[green]Present[/green]' if value else '[red]Missing[/red]'}")

    # Show all keyring entries
    console.print("\n[bold]Keyring entries:[/bold]")
    result = ctx.obj.auth.keyring.list_credentials()
    if result.success and result.data:
        for key in result.data['keys']:
            console.print(f"  • {key}")
    else:
        console.print("[red]No credentials found[/red]")

    # Check default token
    default_token = ctx.obj.auth.keyring.get_credential('github_token_default')
    console.print(f"\nDefault token status: {'[green]Present[/green]' if default_token else '[red]Not found[/red]'}")

@auth.command()
def debug_service():
    """Debug auth service configuration"""
    service = AuthService()
    console.print("\n[bold]Auth Service Debug:[/bold]")
    console.print(f"Config attribute exists: {hasattr(service, 'config')}")
    console.print(f"Available attributes: {dir(service)}")
    
    if hasattr(service, 'config'):
        console.print("\n[bold]Config Contents:[/bold]")
        console.print(service.config._config)

@auth.command()
@click.option('--name', prompt='Your name')
@click.option('--email', prompt='Your email')
@click.pass_context
def setup_signing(ctx, name, email):
    """Setup GPG key for commit signing"""
    console.print(Panel(
        "\n[bold]Setting up GPG signing key[/bold]\n\n"
        "This will:\n"
        "1. Generate a new GPG key\n"
        "2. Configure Git to use it for signing commits\n"
        "3. Enable commit signing by default\n",
        title="GPG Setup"
    ))

    if not click.confirm("Continue?"):
        return

    try:
        # Generate GPG key
        result = ctx.obj.auth.gpg.generate_key(name, email)
        if not result.success:
            console.print(f"[red]✗[/red] Failed to generate GPG key: {result.message}")
            return

        key_id = result.data['key_id']
        
        # Configure Git
        subprocess.run(['git', 'config', '--global', 'user.signingkey', key_id], check=True)
        subprocess.run(['git', 'config', '--global', 'commit.gpgsign', 'true'], check=True)
        
        # Export public key
        public_key = ctx.obj.auth.gpg.export_public_key(key_id)
        if public_key:
            console.print("\n[bold]Your GPG public key (copy everything between the BEGIN and END markers):[/bold]\n")
            # Print without panel, just the raw key
            console.print(public_key)
            
            console.print("\n[bold yellow]Next steps:[/bold yellow]")
            console.print("1. Copy the entire key block above (including BEGIN and END lines)")
            console.print("2. Go to GitHub → Settings → SSH and GPG keys")
            console.print("3. Click 'New GPG key'")
            console.print("4. Paste the key and save")
        
        console.print("\n[green]✓[/green] GPG signing configured successfully!")
        console.print("Your commits will now be signed by default.")
    
    except Exception as e:
        console.print(f"[red]✗[/red] Setup failed: {str(e)}")
        console.print("\nTo remove incomplete setup:")
        console.print("  guardian config unset user.signingkey")
        console.print("  guardian config unset commit.gpgsign")
