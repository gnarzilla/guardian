# src/guardian/cli/commands/keys.py
import click
import json
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from pathlib import Path
from guardian.services.key_management import KeyManager
from guardian.services.key_tracking import KeyTracker
from guardian.services.alerts import KeyAlertSystem
console = Console()

@click.group()
def keys():
    """SSH key management commands"""
    pass

@keys.command()
@click.argument('key_path', type=click.Path(exists=True))
@click.pass_context
def health(ctx, key_path):
    """Check health of SSH key"""
    manager = KeyManager()
    result = manager.check_key_health(Path(key_path))
    
    if result.success:
        health = result.data['health']
        
        console.print(Panel(
            "\n".join([
                f"Age: [cyan]{health['age_days']}[/cyan] days",
                f"Algorithm: [cyan]{health['algorithm']}[/cyan]",
                f"Key Size: [cyan]{health['key_size']}[/cyan] bits",
                f"Permissions OK: {'[green]Yes[/green]' if health['permissions_ok'] else '[red]No[/red]'}",
                "",
                *([f"[yellow]Recommendations:[/yellow]"] + 
                  [f"• {r}" for r in health['recommendations']] 
                  if health['recommendations'] else 
                  ["[green]No issues found[/green]"])
            ]),
            title="Key Health Check"
        ))
    else:
        console.print(f"[red]✗[/red] {result.message}")

@keys.command()
@click.option('--email', prompt='Email for new key')
@click.option('--no-backup', is_flag=True, help='Skip backup of existing keys')
@click.pass_context
def rotate(ctx, email, no_backup):
    """Rotate SSH keys"""
    if not no_backup:
        console.print("[yellow]Will backup existing keys before rotation[/yellow]")
    
    if click.confirm("Continue with key rotation?"):
        manager = KeyManager()
        result = manager.rotate_keys(email, backup=not no_backup)
        
        if result.success:
            console.print(f"[green]✓[/green] {result.message}")
            if result.data.get('backup'):
                console.print(f"Backup created at: {result.data['backup']['backup_path']}")
            console.print(f"New key generated at: {result.data['new_key']}")
        else:
            console.print(f"[red]✗[/red] {result.message}")

@keys.command()
@click.option('--password', prompt=True, hide_input=True,
              confirmation_prompt=True, help='Password for encryption')
@click.pass_context
def backup(ctx, password):
    """Create encrypted backup of all keys"""
    manager = KeyManager()
    result = manager.create_recovery_bundle(password)
    
    if result.success:
        console.print(f"[green]✓[/green] {result.message}")
        console.print(f"Bundle created at: {result.data['bundle_path']}")
        console.print("\n[yellow]Store this bundle and password securely![/yellow]")
    else:
        console.print(f"[red]✗[/red] {result.message}")

@keys.command()
@click.argument('key_path', type=click.Path(exists=True))
@click.pass_context
def track(ctx, key_path):
    """Start tracking key usage"""
    tracker = KeyTracker()
    result = tracker.register_key(Path(key_path))
    
    if result.success:
        console.print(f"[green]✓[/green] {result.message}")
        console.print(f"Key ID: {result.data['key_id']}")
    else:
        console.print(f"[red]✗[/red] {result.message}")

@keys.command()
@click.argument('key_path', type=click.Path(exists=True))
@click.pass_context
def usage(ctx, key_path):
    """Show key usage statistics"""
    tracker = KeyTracker()
    result = tracker.get_key_usage(Path(key_path))
    
    if result.success:
        usage = result.data['usage']
        
        console.print(Panel(
            "\n".join([
                f"Last Used: [cyan]{usage['last_used']}[/cyan]",
                f"Total Uses: [cyan]{usage['usage_count']}[/cyan]",
                f"Success Rate: [cyan]{usage['success_rate']*100:.1f}%[/cyan]",
                "",
                "[bold]Recent Hosts:[/bold]",
                *[f"• {host}" for host in usage['hosts']],
                "",
                "[bold]Platforms:[/bold]",
                *[f"• {platform}" for platform in usage['platforms']]
            ]),
            title="Key Usage Statistics"
        ))
        
        # Check for patterns
        pattern_result = tracker.analyze_usage_patterns(Path(key_path))
        if pattern_result.success and pattern_result.data['patterns']['unusual_activity']:
            console.print("\n[yellow]Unusual Activity Detected:[/yellow]")
            for activity in pattern_result.data['patterns']['unusual_activity']:
                console.print(f"• {activity}")
    else:
        console.print(f"[red]✗[/red] {result.message}")
# src/guardian/cli/commands/keys.py (add these commands)

@keys.command()
@click.pass_context
def alerts(ctx):
    """Show recent security alerts"""
    alert_system = KeyAlertSystem()
    alert_history = Path(alert_system.alert_history)
    
    if not alert_history.exists():
        console.print("No alerts recorded")
        return
    
    try:
        alerts = json.loads(alert_history.read_text())
        
        if not alerts:
            console.print("No alerts recorded")
            return
        
        # Group alerts by level
        grouped = {'critical': [], 'warning': [], 'info': []}
        for alert in alerts:
            grouped[alert['level']].append(alert)
        
        # Show alerts by severity
        for level in ['critical', 'warning', 'info']:
            if grouped[level]:
                console.print(f"\n[bold]{level.upper()} Alerts:[/bold]")
                for alert in grouped[level]:
                    console.print(Panel(
                        "\n".join([
                            f"Time: {alert['timestamp']}",
                            f"Message: {alert['message']}",
                            "",
                            "[bold]Details:[/bold]",
                            *[f"• {k}: {v}" for k, v in alert['details'].items()],
                            "",
                            "[bold]Recommendations:[/bold]",
                            *[f"• {r}" for r in alert['recommendations']]
                        ]),
                        style="red" if level == 'critical' else 
                              "yellow" if level == 'warning' else "blue"
                    ))
    except Exception as e:
        console.print(f"[red]Error reading alerts: {e}[/red]")

@keys.command()
@click.option('--level', 
              type=click.Choice(['critical', 'warning', 'info', 'all']),
              default='all',
              help='Alert level to clear')
@click.pass_context
def clear_alerts(ctx, level):
    """Clear stored alerts"""
    if not click.confirm("Are you sure you want to clear alerts?"):
        return
    
    alert_system = KeyAlertSystem()
    alert_history = Path(alert_system.alert_history)
    
    if not alert_history.exists():
        console.print("No alerts to clear")
        return
    
    try:
        if level == 'all':
            alert_history.write_text('[]')
            console.print("[green]✓[/green] All alerts cleared")
        else:
            alerts = json.loads(alert_history.read_text())
            alerts = [a for a in alerts if a['level'] != level]
            alert_history.write_text(json.dumps(alerts, indent=2))
            console.print(f"[green]✓[/green] {level.title()} alerts cleared")
    except Exception as e:
        console.print(f"[red]Error clearing alerts: {e}[/red]")
