# src/guardian/services/platforms/github.py
class GitHubPlatform(GitPlatform):
    """GitHub-specific implementation"""
    
    def _create_session(self):
        session = requests.Session()
        session.headers.update({
            'Authorization': f'Bearer {self.token}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'Guardian-Git-Tool'
        })
        return session
    
    def get_issues(self, owner: str, repo: str) -> List[IssueData]:
        response = self.session.get(
            f"https://api.github.com/repos/{owner}/{repo}/issues"
        )
        response.raise_for_status()
        
        issues = []
        for item in response.json():
            issues.append(IssueData(
                id=str(item['number']),
                title=item['title'],
                description=item['body'] or '',
                state=item['state'],
                created_at=datetime.fromisoformat(item['created_at'].rstrip('Z')),
                updated_at=datetime.fromisoformat(item['updated_at'].rstrip('Z')),
                labels=[l['name'] for l in item['labels']],
                assignees=[a['login'] for a in item['assignees']],
                comments=item['comments'],
                platform_specific={
                    'node_id': item['node_id'],
                    'url': item['html_url']
                }
            ))
        return issues

    def migrate_to(self, target_platform: GitPlatform,
                   source_repo: str, target_repo: str)
