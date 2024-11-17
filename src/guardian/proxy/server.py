# src/guardian/proxy/server.py
from mitmproxy import ctx, http
from typing import Optional
from .logging import GuardianLogger

class GuardianAuthProxy:
    """Guardian authentication proxy addon for mitmproxy"""
    
    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
        self.logger = GuardianLogger()
    
    def request(self, flow: http.HTTPFlow) -> None:
        """Handle incoming requests"""
        try:
            # Handle direct requests to proxy
            if flow.request.pretty_host == "127.0.0.1" and \
               str(flow.request.port) in ["8080", "8081"]:
                flow.response = http.Response.make(
                    200,
                    b"Guardian Proxy Running",
                    {"Content-Type": "text/plain"}
                )
                return
            
            # Log request
            self.logger.request(
                flow.request.method,
                flow.request.url
            )
            
            # Check for auth requirements
            domain = flow.request.pretty_host
            if self.needs_auth(domain):
                self.handle_auth(flow, domain)
                
        except Exception as e:
            self.logger.error(str(e))
    
    def response(self, flow: http.HTTPFlow) -> None:
        """Handle responses"""
        try:
            # Log response
            self.logger.request(
                flow.request.method,
                flow.request.url,
                flow.response.status_code
            )
        except Exception as e:
            self.logger.error(str(e))
    
    def needs_auth(self, domain: str) -> bool:
        """Check if domain requires authentication"""
        return domain in self.config.get('auth', {}).get('sites', {})
    
    def handle_auth(self, flow: http.HTTPFlow, domain: str) -> None:
        """Handle authentication for domain"""
        self.logger.auth(f"Authentication needed for {domain}")
