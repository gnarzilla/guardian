# src/guardian/services/platforms/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime

@dataclass
class IssueData:
    """Common issue format across platforms"""
    id: str
    title: str
    description: str
    state: str
    created_at: datetime
    updated_at: datetime
    labels: List[str]
    assignees: List[str]
    comments: int
    platform_specific: Dict[str, Any]

@dataclass
class PRData:
    """Common pull request format across platforms"""
    id: str
    title: str
    description: str
    state: str
    source_branch: str
    target_branch: str
    created_at: datetime
    updated_at: datetime
    labels: List[str]
    reviewers: List[str]
    comments: int
    platform_specific: Dict[str, Any]

class GitPlatform(ABC):
    """Base class for platform-specific operations"""
    
    def __init__(self, token: str):
        self.token = token
        self.session = self._create_session()
    
    @abstractmethod
    def _create_session(self):
        """Create authenticated session"""
        pass
    
    @abstractmethod
    def get_issues(self, owner: str, repo: str) -> List[IssueData]:
        """Get repository issues"""
        pass
    
    @abstractmethod
    def get_pull_requests(self, owner: str, repo: str) -> List[PRData]:
        """Get repository pull requests"""
        pass
    
    @abstractmethod
    def migrate_to(self, target_platform: 'GitPlatform', 
                   source_repo: str, target_repo: str) -> bool:
        """Migrate repository to another platform"""
        pass
