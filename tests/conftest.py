# tests/conftest.py
import pytest
from pathlib import Path
import tempfile
import shutil
import os
from guardian.core.auth import AuthService
from guardian.core.config import ConfigService
from guardian.core.repo import RepoService
from guardian.core.security import SecurityService

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def home_dir(temp_dir):
    """Mock home directory for testing"""
    old_home = os.environ.get('HOME')
    os.environ['HOME'] = str(temp_dir)
    yield temp_dir
    if old_home:
        os.environ['HOME'] = old_home

@pytest.fixture
def auth_service(home_dir):
    """Provide a clean AuthService instance"""
    return AuthService()

@pytest.fixture
def config_service(home_dir):
    """Provide a clean ConfigService instance"""
    return ConfigService()

@pytest.fixture
def repo_service(home_dir):
    """Provide a clean RepoService instance"""
    return RepoService()

@pytest.fixture
def security_service(home_dir):
    """Provide a clean SecurityService instance"""
    return SecurityService()

@pytest.fixture
def sample_repo(temp_dir):
    """Create a sample git repository"""
    repo_dir = temp_dir / 'sample-repo'
    repo_dir.mkdir()
    os.chdir(repo_dir)
    os.system('git init')
    return repo_dir

