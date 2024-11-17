# src/guardian/auth/handlers.py
from typing import Dict, Optional, Type
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
import requests
from bs4 import BeautifulSoup

@dataclass
class AuthResult:
    """Authentication result with session data"""
    success: bool
    session_data: Optional[Dict] = None
    expires_at: Optional[datetime] = None
    refresh_token: Optional[str] = None
    error: Optional[str] = None

class BaseAuthHandler:
    """Base handler with common functionality"""
    
    def __init__(self, site_config: Dict):
        self.config = site_config
        self.session = requests.Session()
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def authenticate(self) -> AuthResult:
        """Main authentication method"""
        raise NotImplementedError
    
    def _extract_form_data(self, html: str, form_id: str) -> Dict:
        """Extract form fields including hidden ones"""
        soup = BeautifulSoup(html, 'html.parser')
        form = soup.find('form', id=form_id)
        if not form:
            return {}
            
        data = {}
        for input_field in form.find_all('input'):
            if 'name' in input_field.attrs:
                data[input_field['name']] = input_field.get('value', '')
        return data

class OAuthHandler(BaseAuthHandler):
    """Generic OAuth 2.0 handler with site-specific extensions"""
    
    SITE_SPECIFICS = {
        'google.com': {
            'auth_url': 'https://accounts.google.com/o/oauth2/v2/auth',
            'token_url': 'https://oauth2.googleapis.com/token',
            'extra_params': {'prompt': 'consent'},
        },
        'github.com': {
            'auth_url': 'https://github.com/login/oauth/authorize',
            'token_url': 'https://github.com/login/oauth/access_token',
            'headers': {'Accept': 'application/json'},
        }
    }
    
    async def authenticate(self) -> AuthResult:
        site = self.config['domain']
        specifics = self.SITE_SPECIFICS.get(site, {})
        
        try:
            token = await self._oauth_flow(
                auth_url=specifics.get('auth_url', self.config['auth_url']),
                token_url=specifics.get('token_url', self.config['token_url']),
                extra_params=specifics.get('extra_params', {}),
                headers=specifics.get('headers', {})
            )
            
            return AuthResult(
                success=True,
                session_data={'token': token['access_token']},
                expires_at=datetime.now() + timedelta(seconds=token['expires_in']),
                refresh_token=token.get('refresh_token')
            )
            
        except Exception as e:
            self.logger.error(f"OAuth authentication failed for {site}: {e}")
            return AuthResult(success=False, error=str(e))

class SessionHandler(BaseAuthHandler):
    """Form-based session handler with site-specific adjustments"""
    
    SITE_SPECIFICS = {
        'facebook.com': {
            'form_id': 'login_form',
            'success_cookies': ['c_user'],
            'extra_headers': {'User-Agent': 'Mozilla/5.0...'},
        },
        'twitter.com': {
            'form_id': 'signin-form',
            'success_cookies': ['auth_token'],
            'csrf_token': True,
        }
    }
    
    async def authenticate(self) -> AuthResult:
        site = self.config['domain']
        specifics = self.SITE_SPECIFICS.get(site, {})
        
        try:
            # Get login page
            response = await self._get_login_page(
                headers=specifics.get('extra_headers', {})
            )
            
            # Extract form data
            form_data = self._extract_form_data(
                response.text,
                specifics.get('form_id', 'login_form')
            )
            
            # Add credentials
            form_data.update(self.config['credentials'])
            
            # Handle CSRF if needed
            if specifics.get('csrf_token'):
                form_data['csrf_token'] = self._extract_csrf_token(response.text)
            
            # Submit login
            login_response = await self._submit_login(form_data)
            
            # Check success based on site-specific cookies
            success_cookies = specifics.get('success_cookies', ['sessionid'])
            if any(c in self.session.cookies for c in success_cookies):
                return AuthResult(
                    success=True,
                    session_data={'cookies': self.session.cookies.get_dict()}
                )
            
            return AuthResult(
                success=False,
                error="Login failed - required cookies not found"
            )
            
        except Exception as e:
            self.logger.error(f"Session authentication failed for {site}: {e}")
            return AuthResult(success=False, error=str(e))

class HandlerRegistry:
    """Registry of authentication handlers"""
    
    _handlers: Dict[str, Type[BaseAuthHandler]] = {
        'oauth': OAuthHandler,
        'session': SessionHandler
    }
    
    @classmethod
    def get_handler(cls, auth_type: str, site_config: Dict) -> BaseAuthHandler:
        """Get appropriate handler for site"""
        handler_class = cls._handlers.get(auth_type)
        if not handler_class:
            raise ValueError(f"Unsupported auth type: {auth_type}")
        return handler_class(site_config)
