# src/guardian/services/api/__init__.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
import requests
from datetime import datetime, timezone
import jwt  # For JWT token parsing

@dataclass
class TokenInfo:
    """Common token information across platforms"""
    valid: bool
    user: str
    scopes: List[str]
    expires_at: Optional[datetime]
    rate_limit_remaining: Optional[int]
    capabilities: List[str]
    raw_data: Dict[str, Any]  # Platform-specific data

class GitPlatformAPI(ABC):
    """Base class for Git platform APIs"""
    
    def __init__(self, token: str):
        self.token = token
        self.session = requests.Session()
    
    @abstractmethod
    def validate_token(self) -> TokenInfo:
        """Validate token and return token information"""
        pass
    
    @abstractmethod
    def get_user(self) -> Dict[str, Any]:
        """Get authenticated user information"""
        pass
    
    @property
    @abstractmethod
    def base_url(self) -> str:
        """Base URL for API endpoints"""
        pass

class GitHubAPI(GitPlatformAPI):
    """GitHub API implementation"""
    
    base_url = "https://api.github.com"
    
    def __init__(self, token: str):
        super().__init__(token)
        self.session.headers.update({
            'Authorization': f'Bearer {token}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'Guardian-Git-Tool'
        })
    
    def validate_token(self) -> TokenInfo:
        """
        Validate GitHub token and get detailed information
        
        Checks:
        1. Token validity
        2. Scopes and permissions
        3. User information
        4. Rate limit status
        5. Token expiration (if applicable)
        """
        try:
            # Check basic authentication
            user_response = self.session.get(f"{self.base_url}/user")
            user_response.raise_for_status()
            user_data = user_response.json()
            
            # Get rate limit information
            rate_limit = self.session.get(f"{self.base_url}/rate_limit")
            rate_limit_data = rate_limit.json()
            
            # Get token metadata (requires preview header)
            token_response = self.session.get(
                f"{self.base_url}/applications/token",
                headers={'Accept': 'application/vnd.github.v3+json'}
            )
            token_data = token_response.json() if token_response.ok else {}
            
            # Parse scopes
            scopes = user_response.headers.get('X-OAuth-Scopes', '').split(',')
            scopes = [s.strip() for s in scopes if s.strip()]
            
            # Check expiration
            expires_at = None
            if 'exp' in token_data:
                expires_at = datetime.fromtimestamp(token_data['exp'], timezone.utc)
            
            # Map scopes to capabilities
            capabilities = self._get_capabilities(scopes)
            
            return TokenInfo(
                valid=True,
                user=user_data['login'],
                scopes=scopes,
                expires_at=expires_at,
                rate_limit_remaining=rate_limit_data['resources']['core']['remaining'],
                capabilities=capabilities,
                raw_data={
                    'user': user_data,
                    'rate_limit': rate_limit_data,
                    'token_metadata': token_data
                }
            )
            
        except requests.exceptions.RequestException as e:
            if e.response and e.response.status_code == 401:
                return TokenInfo(
                    valid=False,
                    user='',
                    scopes=[],
                    expires_at=None,
                    rate_limit_remaining=None,
                    capabilities=[],
                    raw_data={'error': str(e)}
                )
            raise
    
    def _get_capabilities(self, scopes: List[str]) -> List[str]:
        """Map OAuth scopes to human-readable capabilities"""
        capability_map = {
            'repo': [
                'Access private repositories',
                'Clone and push code',
                'Manage repository settings'
            ],
            'read:org': [
                'View organization membership',
                'Read team information'
            ],
            'admin:public_key': [
                'Manage SSH keys',
                'Configure deploy keys'
            ],
            'gist': [
                'Create and manage gists'
            ],
            'notifications': [
                'Access notifications',
                'Mark as read'
            ],
            'delete_repo': [
                'Delete repositories'
            ]
            # Add more scope mappings as needed
        }
        
        capabilities = []
        for scope in scopes:
            if scope in capability_map:
                capabilities.extend(capability_map[scope])
        return capabilities
    
    def get_user(self) -> Dict[str, Any]:
        """Get authenticated user information"""
        response = self.session.get(f"{self.base_url}/user")
        response.raise_for_status()
        return response.json()

# We can add more platform implementations as needed:
# class GitLabAPI(GitPlatformAPI):
#     base_url = "https://gitlab.com/api/v4"
#     ...

# class BitbucketAPI(GitPlatformAPI):
#     base_url = "https://api.bitbucket.org/2.0"
#     ...
