# src/guardian/cli/commands/repo.py
import click
from rich.console import Console
from rich.panel import Panel
import subprocess
from pathlib import Path
from guardian.services.git import GitService

console = Console()

@click.group()
def repo():
    """Repository and remote management commands"""
    pass

@repo.command()
@click.option('--remote-type', type=click.Choice(['github', 'gitlab', 'bitbucket', 'custom']),
              help='Remote platform type')
@click.option('--private', is_flag=True, default=True, help='Create private repository')
@click.pass_context
def create(ctx, remote_type: str, private: bool):
    """Create a remote repository for the current project"""
    try:
        # Verify we're in a git repository
        if not Path('.git').exists():
            # Initialize if not exists
            if click.confirm("Not a git repository. Initialize one?"):
                subprocess.run(['git', 'init'], check=True)
            else:
                return
        
        # Get project name from directory
        project_name = Path.cwd().name
        
        # Show creation plan
        console.print(Panel(
            f"Creating remote repository:\n\n"
            f"Project: {project_name}\n"
            f"Platform: {remote_type}\n"
            f"Visibility: {'Private' if private else 'Public'}\n",
            title="Repository Creation"
        ))
        
        if not click.confirm("Continue?"):
            return
        
        with console.status("Creating repository..."):
            if remote_type == 'github':
                # Use GitHub API through configured token
                # This would be handled by a separate GitHub service
                pass
            elif remote_type == 'gitlab':
                # GitLab API implementation
                pass
            # ... other platforms
            
            # Add remote to local repo
            # Set up branch tracking
            # Configure additional remote settings
        
        console.print("\n[green]✓[/green] Remote repository created successfully!")
        console.print("\nNext steps:")
        console.print("1. Review repository settings")
        console.print("2. Push your changes: git push -u origin main")
        
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to create repository: {str(e)}")

@repo.command()
@click.option('--remote-type', type=click.Choice(['github', 'gitlab', 'bitbucket', 'custom']),
              help='Remote platform type for authentication')
@click.argument('url')
@click.pass_context
def connect(ctx, remote_type: str, url: str):
    """Connect existing repository to a remote"""
    try:
        if not Path('.git').exists():
            console.print("[red]✗[/red] Not a git repository")
            return
        
        # Verify/setup authentication for the platform
        auth_result = ctx.obj.auth.verify_platform_auth(remote_type)
        if not auth_result.success:
            if click.confirm("Authentication not setup. Configure now?"):
                # Guide through platform-specific auth setup
                if remote_type == 'github':
                    ctx.invoke(auth_setup_github)
                # ... other platforms
            else:
                return
        
        # Add the remote
        subprocess.run(['git', 'remote', 'add', 'origin', url], check=True)
        
        console.print("[green]✓[/green] Remote connected successfully!")
        console.print("\nNext steps:")
        console.print("1. Verify connection: git remote -v")
        console.print("2. Push your changes: git push -u origin main")
        
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to connect repository: {str(e)}")

@repo.command()
@click.pass_context
def sync(ctx):
    """Synchronize repository configuration across systems"""
    try:
        # Export current configuration
        config_data = {
            'remotes': {},
            'hooks': {},
            'git_config': {}
        }
        
        # Get remote information
        remotes = subprocess.run(
            ['git', 'remote', '-v'],
            capture_output=True, text=True, check=True
        ).stdout
        
        for line in remotes.splitlines():
            if line:
                name, url, _ = line.split()
                config_data['remotes'][name] = url
        
        # Get hook configurations
        hooks_dir = Path('.git/hooks')
        if hooks_dir.exists():
            for hook in hooks_dir.glob('*'):
                if hook.is_file():
                    config_data['hooks'][hook.name] = {
                        'enabled': hook.stat().st_mode & 0o111 != 0,
                        'guardian_managed': 'Guardian' in hook.read_text()
                    }
        
        # Get git config
        for key in ['user.name', 'user.email', 'user.signingkey']:
            try:
                value = subprocess.run(
                    ['git', 'config', '--get', key],
                    capture_output=True, text=True, check=True
                ).stdout.strip()
                config_data['git_config'][key] = value
            except subprocess.CalledProcessError:
                pass
        
        # Export to file
        config_file = Path('.guardian-sync.yml')
        import yaml
        with open(config_file, 'w') as f:
            yaml.safe_dump(config_data, f)
        
        console.print(f"[green]✓[/green] Configuration exported to {config_file}")
        console.print("\nTo use this configuration on another system:")
        console.print(f"1. Copy {config_file} to the project directory")
        console.print("2. Run: guardian repo apply-sync")
        
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to sync configuration: {str(e)}")

@repo.command()
@click.pass_context
def apply_sync(ctx):
    """Apply synchronized configuration from .guardian-sync.yml"""
    try:
        config_file = Path('.guardian-sync.yml')
        if not config_file.exists():
            console.print("[red]✗[/red] No sync configuration found")
            return
        
        import yaml
        with open(config_file) as f:
            config_data = yaml.safe_load(f)
        
        # Apply configuration
        with console.status("Applying configuration..."):
            # Setup remotes
            for name, url in config_data.get('remotes', {}).items():
                try:
                    subprocess.run(['git', 'remote', 'add', name, url], check=True)
                except subprocess.CalledProcessError:
                    # Remote might already exist
                    pass
            
            # Setup hooks
            for hook, info in config_data.get('hooks', {}).items():
                if info.get('guardian_managed'):
                    ctx.invoke(hooks_install)
            
            # Apply git config
            for key, value in config_data.get('git_config', {}).items():
                subprocess.run(['git', 'config', key, value], check=True)
        
        console.print("[green]✓[/green] Configuration applied successfully!")
        
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to apply configuration: {str(e)}")

@repo.command()
@click.argument('path', type=click.Path(exists=True))
@click.option('--remote', default='origin', help='Remote name')
@click.option('--branch', help='Branch to push')
@click.pass_context
def push(ctx, path, remote, branch):
    """Push changes to remote repository"""
    try:
        path = Path(path)
        
        # Ensure it's a Git repository
        if not (path / '.git').exists():
            console.print("[red]✗ Not a git repository[/red]")
            return
        
        # Check authentication status
        auth_status = ctx.obj.auth.check_auth_status()
        if not auth_status.success:
            console.print("[yellow]⚠ Authentication issues detected:[/yellow]")
            for issue in auth_status.data.get('issues', []):
                console.print(f"  • {issue}")
            if not click.confirm("Continue anyway?"):
                console.print("[red]✗ Push canceled[/red]")
                return
        
        # Construct the Git push command
        cmd = ['git', 'push', remote]
        if branch:
            cmd.append(branch)
        
        # Execute the push command
        result = subprocess.run(cmd, cwd=path, capture_output=True, text=True)
        if result.returncode == 0:
            console.print("[green]✓ Push successful[/green]")
        else:
            console.print("[red]✗ Push failed[/red]")
            console.print(result.stderr.strip())
    
    except Exception as e:
        console.print(f"[red]✗ Error: {str(e)}[/red]")

@repo.command()
@click.argument('url')
@click.option('--path', type=click.Path(), help='Local path to clone into')
@click.pass_context
def pull(ctx, url, path):
    """Pull from remote repository"""
    try:
        if path:
            path = Path(path)
        else:
            path = Path('.')
            
        cmd = ['git', 'pull']
        if url:
            cmd.extend(['origin', url])
            
        result = subprocess.run(cmd, cwd=path, capture_output=True, text=True)
        if result.returncode == 0:
            console.print("[green]✓[/green] Pull successful")
        else:
            console.print(f"[red]✗[/red] Pull failed: {result.stderr}")
            
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {str(e)}")

# Update the status command to handle all platforms
@repo.command()
@click.pass_context
def status(ctx):
    """Check repository status and remote connection"""
    git_service = GitService()
    
    # Check current branch
    branch_result = git_service.get_current_branch()
    if branch_result.success:
        console.print(Panel(
            f"Current branch: [green]{branch_result.data['branch']}[/green]",
            title="Local Status"
        ))
        
        # Check remote connection
        remote_result = git_service.check_remote()
        if remote_result.success:
            platform = remote_result.data['platform']
            # Get appropriate token
            token = ctx.obj.auth.keyring.get_credential(f'{platform}_token_default')
            if token:
                # Verify repository
                verify_result = git_service.verify_repo(
                    platform,
                    token,
                    remote_result.data['owner'],
                    remote_result.data['repo']
                )
                
                if verify_result.success:
                    console.print(Panel(
                        "\n".join([
                            f"Platform: [cyan]{platform.title()}[/cyan]",
                            f"Owner: [cyan]{remote_result.data['owner']}[/cyan]",
                            f"Repository: [cyan]{remote_result.data['repo']}[/cyan]",
                            f"Default branch: [cyan]{verify_result.data['default_branch']}[/cyan]",
                            f"Private: [cyan]{verify_result.data['private']}[/cyan]",
                            "",
                            "[bold]Permissions:[/bold]",
                            *[f"• {k}: [green]Yes[/green]" if v else f"• {k}: [red]No[/red]"
                              for k, v in verify_result.data['permissions'].items()]
                        ]),
                        title=f"{platform.title()} Status"
                    ))
                    
                    # Check if on default branch
                    if branch_result.data['branch'] != verify_result.data['default_branch']:
                        console.print(f"[yellow]Note: You are not on the default branch ({verify_result.data['default_branch']})[/yellow]")
                else:
                    console.print(f"[yellow]{verify_result.message}[/yellow]")
            else:
                console.print(f"[yellow]No {platform.title()} token configured[/yellow]")
                console.print(f"Run: guardian auth setup-{platform}")
        else:
            console.print("[yellow]Not connected to a remote repository[/yellow]")
    else:
        console.print("[red]Not a git repository[/red]")

@repo.group()
def migrate():
    """Repository migration commands"""
    pass

@migrate.command()
@click.argument('source_repo')
@click.argument('target_platform')
@click.option('--target-repo', help='Target repository name (default: same as source)')
@click.pass_context
def plan(ctx, source_repo, target_platform, target_repo):
    """Plan repository migration"""
    git_service = GitService()
    
    # Get source platform
    remote_result = git_service.check_remote(Path(source_repo))
    if not remote_result.success:
        console.print("[red]✗[/red] Could not determine source platform")
        return
    
    source_platform = remote_result.data['platform']
    target_repo = target_repo or remote_result.data['repo']
    
    # Create migration planner
    try:
        source = create_platform(source_platform, ctx.obj.auth)
        target = create_platform(target_platform, ctx.obj.auth)
        
        migration = PlatformMigration(source, target)
        plan = migration.create_migration_plan(source_repo, target_repo)
        
        # Show migration plan
        console.print(Panel(
            "\n".join([
                f"Source: [cyan]{plan.source_platform}[/cyan] ({plan.source_repo})",
                f"Target: [cyan]{plan.target_platform}[/cyan] ({plan.target_repo})",
                "",
                "[bold]Items to migrate:[/bold]",
                *[f"• {item}: {'[green]Yes[/green]' if enabled else '[red]No[/red]'}"
                  for item, enabled in plan.items.items()],
                "",
                f"Estimated time: [yellow]{plan.estimated_time}[/yellow] minutes"
            ]),
            title="Migration Plan"
        ))
        
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to create migration plan: {str(e)}")

@migrate.command()
@click.argument('source_repo')
@click.argument('target_platform')
@click.option('--target-repo', help='Target repository name')
@click.option('--skip', multiple=True, 
              type=click.Choice(['issues', 'pull_requests', 'wiki', 'actions']),
              help='Items to skip during migration')
@click.pass_context
def execute(ctx, source_repo, target_platform, target_repo, skip):
    """Execute repository migration"""
    # Similar to plan, but executes the migration
    pass
