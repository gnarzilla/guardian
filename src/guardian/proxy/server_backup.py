# src/guardian/proxy/server.py
from mitmproxy import ctx, http
from mitmproxy.http import HTTPFlow
import sqlite3
import jwt
from datetime import datetime
from typing import Dict, Optional
from pathlib import Path
import logging

class GuardianAuthProxy:
    """Guardian authentication proxy addon for mitmproxy"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.db_path = Path.home() / '.guardian' / 'proxy.db'
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(self.db_path))
        self.sessions: Dict[str, Dict] = {}
        self.logger = logging.getLogger(__name__)
        self.setup_logging()
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite database"""
        with self.db:
            self.db.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    domain TEXT PRIMARY KEY,
                    session_data TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    expires_at DATETIME,
                    last_used DATETIME
                )
            """)

    def setup_logging(self):
        """Setup logging configuration"""
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s -  %(levelname)s - %(message)s'
        )
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

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

            # Log the request
            self.logger.info(f"Request: {flow.request.method} {flow.request.url}")
            
            # Continue with normal proxy behavior for other requests
            domain = flow.request.pretty_host
            if self.needs_auth(domain):
                self.handle_auth(flow, domain)
                
        except Exception as e:
            self.logger.error(f"Error handling request: {e}")

    def response(self, flow: http.HTTPFlow) -> None:
        """Handle responses"""
        try:
            # Log the response
            self.logger.info(
                f"Response: {flow.response.status_code} {flow.request.url}"
            )
        except Exception as e:
            self.logger.error(f"Error handling response: {e}")
    
    def needs_auth(self, domain: str) -> bool:
        """Check if domain requires authentication"""
        return domain in self.config.get('auth', {}).get('sites', {})
    
    def get_valid_session(self, domain: str) -> Optional[Dict]:
        """Get valid session for domain if exists"""
        try:
            cur = self.db.execute(
                """
                SELECT session_data, expires_at 
                FROM sessions 
                WHERE domain = ? 
                  AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
                """,
                (domain,)
            )
            row = cur.fetchone()
            
            if row:
                import json
                session_data = json.loads(row[0])
                self.db.execute(
                    "UPDATE sessions SET last_used = CURRENT_TIMESTAMP WHERE domain = ?",
                    (domain,)
                )
                return session_data
                
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting session: {e}")
            return None
    
    def handle_auth(self, flow: HTTPFlow, domain: str) -> None:
        """Handle authentication for domain"""
        try:
            site_config = self.config['auth']['sites'].get(domain)
            if not site_config:
                return
                
            # Log authentication attempt
            self.logger.info(f"Authentication needed for {domain}")
            
        except Exception as e:
            self.logger.error(f"Error in auth handling: {e}")
    
    def inject_session(self, flow: HTTPFlow, session: Dict) -> None:
        """Inject session data into request"""
        try:
            if 'cookies' in session:
                # Session cookie-based auth
                cookie_header = '; '.join(
                    f"{k}={v}" for k, v in session['cookies'].items()
                )
                flow.request.headers['Cookie'] = cookie_header
                
            elif 'token' in session:
                # Token-based auth
                token_type = session.get('token_type', 'Bearer')
                flow.request.headers['Authorization'] = \
                    f"{token_type} {session['token']}"
                
        except Exception as e:
            self.logger.error(f"Error injecting session: {e}")

    def done(self):
        """Clean up when proxy stops"""
        if hasattr(self, 'db'):
            self.db.close()
