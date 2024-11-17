# src/guardian/proxy/logging.py
import logging
from rich.console import Console
from rich.logging import RichHandler
from typing import Optional
from urllib.parse import urlparse, parse_qs

console = Console()

class GuardianLogger:
    """Custom logger for Guardian proxy"""
    
    def __init__(self, name: str = "guardian.proxy"):
        self.logger = logging.getLogger(name)
        self._setup_logger()
    
    def _setup_logger(self):
        """Configure logging format and handlers"""
        # Remove existing handlers
        self.logger.handlers.clear()
        
        # Create rich handler
        handler = RichHandler(
            console=console,
            show_time=False,
            show_path=False,
            rich_tracebacks=True,
            tracebacks_show_locals=False
        )
        
        # Set format
        handler.setFormatter(logging.Formatter("%(message)s"))
        
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def _format_url(self, url: str, max_length: int = 100) -> str:
        """Format URL for display"""
        parsed = urlparse(url)
        
        # Hide long query parameters
        if parsed.query:
            query_params = parse_qs(parsed.query)
            short_query = '&'.join(f"{k}=..." for k in query_params.keys())
            url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{short_query}"
        
        if len(url) > max_length:
            return f"{url[:max_length-3]}..."
        return url
    
    def request(self, method: str, url: str, status: Optional[int] = None):
        """Log request"""
        formatted_url = self._format_url(url)
        if status:
            self.logger.info(f"[cyan]{method}[/cyan] {formatted_url} → [green]{status}[/green]")
        else:
            self.logger.info(f"[cyan]{method}[/cyan] {formatted_url}")
    
    def response(self, status: int, url: str):
        """Log response"""
        formatted_url = self._format_url(url)
        color = "green" if 200 <= status < 300 else "yellow" if status < 400 else "red"
        self.logger.info(f"[{color}]{status}[/{color}] {formatted_url}")
    
    def auth(self, message: str):
        """Log authentication events"""
        self.logger.info(f"[magenta]Auth:[/magenta] {message}")
    
    def error(self, message: str):
        """Log errors"""
        self.logger.error(f"[red]Error:[/red] {message}")
    
    def info(self, message: str):
        """Log general information"""
        self.logger.info(message)
