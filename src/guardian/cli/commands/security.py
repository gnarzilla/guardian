# src/guardian/cli/commands/security.py
@cli.group()
def security():
    """Security management commands"""
    pass

@security.command()
@click.argument('path', type=click.Path(exists=True))
@click.pass_context
def scan(ctx, path):
    """Scan repository for sensitive data"""
    result = ctx.obj.security.scan_repo(Path(path))
    if result.success:
        findings = result.data['findings']
        if findings:
            table = Table(title="Security Scan Results")
            table.add_column("Type")
            table.add_column("File")
            table.add_column("Line")
            
            for finding in findings:
                table.add_row(
                    finding['type'],
                    finding['file'],
                    str(finding['line'])
                )
            
            console.print(table)
        else:
            console.print("[green]No security issues found[/green]")
    else:
        console.print(f"[red]Error: {result.message}[/red]")
