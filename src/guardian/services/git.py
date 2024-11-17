# src/guardian/services/git.py
import subprocess
from pathlib import Path
from typing import Optional, Dict, Literal
import re
import requests
from guardian.core import Service, Result

PlatformType = Literal['github', 'gitlab', 'bitbucket']

class GitService(Service):
    """Git operations and status checking"""
    
    PLATFORM_PATTERNS = {
        'github': (
            r'(?:https://github\.com/|git@github\.com:)([^/]+)/([^/.]+)(?:\.git)?'
        ),
        'gitlab': (
            r'(?:https://gitlab\.com/|git@gitlab\.com:)([^/]+)/([^/.]+)(?:\.git)?'
        ),
        'bitbucket': (
            r'(?:https://bitbucket\.org/|git@bitbucket\.org:)([^/]+)/([^/.]+)(?:\.git)?'
        )
    }
    
    API_URLS = {
        'github': 'https://api.github.com',
        'gitlab': 'https://gitlab.com/api/v4',
        'bitbucket': 'https://api.bitbucket.org/2.0'
    }

    def detect_platform(self, remote_url: str) -> Optional[tuple[str, str, str]]:
        """Detect git platform and extract owner/repo"""
        for platform, pattern in self.PLATFORM_PATTERNS.items():
            match = re.match(pattern, remote_url)
            if match:
                return platform, match.group(1), match.group(2)
        return None

    def get_current_branch(self, path: Path = Path('.')) -> Result:
        """Get current branch name"""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                cwd=path,
                capture_output=True,
                text=True,
                check=True
            )
            return self.create_result(
                True,
                "Branch found",
                {'branch': result.stdout.strip()}
            )
        except subprocess.CalledProcessError:
            return self.create_result(
                False,
                "Not a git repository or no branch found"
            )

    def check_remote(self, path: Path = Path('.')) -> Result:
        """Check remote repository details"""
        try:
            remote_url = subprocess.run(
                ['git', 'remote', 'get-url', 'origin'],
                cwd=path,
                capture_output=True,
                text=True,
                check=True
            ).stdout.strip()

            platform_info = self.detect_platform(remote_url)
            if platform_info:
                platform, owner, repo = platform_info
                return self.create_result(
                    True,
                    f"{platform.title()} repository found",
                    {
                        'platform': platform,
                        'owner': owner,
                        'repo': repo,
                        'url': remote_url
                    }
                )
            else:
                return self.create_result(
                    False,
                    "Unknown repository platform"
                )

        except subprocess.CalledProcessError:
            return self.create_result(
                False,
                "No remote origin found"
            )

    def verify_repo(self, platform: str, token: str, owner: str, repo: str) -> Result:
        """Verify repository exists and user has access"""
        try:
            if platform == 'github':
                headers = {
                    'Authorization': f'Bearer {token}',
                    'Accept': 'application/vnd.github.v3+json'
                }
                url = f"{self.API_URLS[platform]}/repos/{owner}/{repo}"
                
            elif platform == 'gitlab':
                headers = {
                    'Authorization': f'Bearer {token}',
                }
                url = f"{self.API_URLS[platform]}/projects/{owner}%2F{repo}"
                
            elif platform == 'bitbucket':
                # Bitbucket uses Basic Auth with app passwords
                headers = {
                    'Authorization': f'Bearer {token}',
                }
                url = f"{self.API_URLS[platform]}/repositories/{owner}/{repo}"
                
            else:
                return self.create_result(
                    False,
                    f"Unsupported platform: {platform}"
                )

            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Platform-specific data parsing
                if platform == 'github':
                    return self.create_result(
                        True,
                        "Repository verified",
                        {
                            'default_branch': data['default_branch'],
                            'permissions': data['permissions'],
                            'private': data['private']
                        }
                    )
                    
                elif platform == 'gitlab':
                    return self.create_result(
                        True,
                        "Repository verified",
                        {
                            'default_branch': data['default_branch'],
                            'permissions': {
                                'admin': data['permissions']['project_access']['access_level'] >= 40,
                                'push': data['permissions']['project_access']['access_level'] >= 30,
                                'pull': data['permissions']['project_access']['access_level'] >= 20,
                            },
                            'private': not data['public']
                        }
                    )
                    
                elif platform == 'bitbucket':
                    return self.create_result(
                        True,
                        "Repository verified",
                        {
                            'default_branch': data['mainbranch']['name'],
                            'permissions': {
                                'admin': 'admin' in data['privileges'],
                                'push': 'write' in data['privileges'],
                                'pull': 'read' in data['privileges'],
                            },
                            'private': not data['is_private']
                        }
                    )
            else:
                return self.create_result(
                    False,
                    f"Repository not found or no access ({response.status_code})"
                )
                
        except Exception as e:
            return self.create_result(
                False,
                f"Failed to verify repository: {str(e)}",
                error=e
            )
