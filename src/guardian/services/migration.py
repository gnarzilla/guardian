# src/guardian/services/migration.py
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import tempfile
import subprocess
from pathlib import Path
import shutil

@dataclass
class MigrationPlan:
    """Plan for repository migration"""
    source_platform: str
    target_platform: str
    source_repo: str
    target_repo: str
    items: Dict[str, bool]  # What to migrate (code, issues, PRs, etc.)
    estimated_time: int     # Estimated minutes

@dataclass
class MigrationResult:
    """Results of migration attempt"""
    success: bool
    items_migrated: Dict[str, int]
    errors: List[str]
    warnings: List[str]

class PlatformMigration:
    """Handles repository migration between platforms"""
    
    def __init__(self, source_platform: GitPlatform, target_platform: GitPlatform):
        self.source = source_platform
        self.target = target_platform
    
    def create_migration_plan(self, 
                            source_repo: str,
                            target_repo: str) -> MigrationPlan:
        """Create a migration plan"""
        # Check what can be migrated
        items = {
            'code': True,            # Base repository
            'branches': True,        # All branches
            'tags': True,           # Version tags
            'releases': True,       # Release information
            'issues': self._can_migrate_issues(),
            'pull_requests': self._can_migrate_prs(),
            'wiki': self._has_wiki(source_repo),
            'actions': self._has_actions(source_repo)
        }
        
        # Estimate time based on repo size and features
        estimated_time = self._estimate_migration_time(source_repo, items)
        
        return MigrationPlan(
            source_platform=self.source.__class__.__name__,
            target_platform=self.target.__class__.__name__,
            source_repo=source_repo,
            target_repo=target_repo,
            items=items,
            estimated_time=estimated_time
        )
    
    def execute_migration(self, plan: MigrationPlan) -> MigrationResult:
        """Execute migration plan"""
        results = MigrationResult(
            success=True,
            items_migrated={},
            errors=[],
            warnings=[]
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                # Clone source repository
                self._clone_repository(plan.source_repo, temp_dir)
                
                # Migrate basics (code, branches, tags)
                self._migrate_code(temp_dir, plan.target_repo, results)
                
                # Migrate additional items if requested
                if plan.items.get('issues'):
                    self._migrate_issues(plan, results)
                
                if plan.items.get('pull_requests'):
                    self._migrate_pull_requests(plan, results)
                
                if plan.items.get('wiki'):
                    self._migrate_wiki(plan, results)
                
                if plan.items.get('actions'):
                    self._migrate_actions(plan, results)
                
            except Exception as e:
                results.success = False
                results.errors.append(str(e))
        
        return results

    def _migrate_issues(self, plan: MigrationPlan, results: MigrationResult):
        """Migrate issues between platforms"""
        try:
            # Get source issues
            source_issues = self.source.get_issues(
                *self._parse_repo_string(plan.source_repo)
            )
            
            migrated = 0
            for issue in source_issues:
                try:
                    # Convert to target platform format
                    converted_issue = self._convert_issue_format(
                        issue,
                        self.source.__class__.__name__,
                        self.target.__class__.__name__
                    )
                    
                    # Create on target platform
                    self.target.create_issue(
                        *self._parse_repo_string(plan.target_repo),
                        converted_issue
                    )
                    migrated += 1
                    
                except Exception as e:
                    results.warnings.append(
                        f"Failed to migrate issue {issue.id}: {str(e)}"
                    )
            
            results.items_migrated['issues'] = migrated
            
        except Exception as e:
            results.errors.append(f"Issue migration failed: {str(e)}")

    def _convert_issue_format(self, issue: IssueData,
                            source_platform: str,
                            target_platform: str) -> Dict[str, Any]:
        """Convert issue format between platforms"""
        # Basic conversion that works across platforms
        converted = {
            'title': issue.title,
            'description': issue.description,
            'state': self._convert_state(issue.state, source_platform, target_platform),
            'labels': issue.labels
        }
        
        # Platform-specific adjustments
        if target_platform == 'GitLab':
            converted['iid'] = issue.id
            if 'type' in issue.labels:
                converted['issue_type'] = issue.labels['type']
                
        elif target_platform == 'Bitbucket':
            converted['content'] = {
                'raw': issue.description
            }
            
        return converted
