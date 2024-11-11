# docs/index.md
# Guardian Documentation

Guardian is a comprehensive Git authentication and development assistant that helps you manage SSH keys, tokens, repository configurations, and security practices.

## Features

### Currently Implemented

🔒 **Authentication Management**
- SSH key generation and management
- GitHub token secure storage
- Git configuration setup

🛠️ **Repository Management**
- Repository initialization
- Template-based project creation
- Pre-commit hook setup

🔐 **Security**
- Sensitive data scanning
- Secure credential storage
- Configuration backup

### Coming Soon

📦 **Enhanced Repository Features**
- Multi-profile support
- Remote repository management
- Branch policy enforcement

🔄 **Automated Workflows**
- Key rotation automation
- Configuration synchronization
- Team settings management

🛡️ **Advanced Security**
- Vulnerability scanning
- Dependency auditing
- Compliance checking

## Quick Links
- [Installation Guide](getting-started/installation.md)
- [Quick Start](getting-started/quickstart.md)
- [API Reference](api/auth.md)
- [Contributing Guide](contributing/setup.md)

# docs/getting-started/quickstart.md
# Quick Start Guide

## Basic Setup

```bash
# Install Guardian
pip install guardian-git

# Initialize SSH authentication
guardian auth ssh --email your@email.com

# Store GitHub token
guardian auth pat

# Configure Git
guardian config setup
```

## Repository Management

```bash
# Initialize new repository
guardian repo init my-project

# Initialize with template
guardian repo init my-project --template python

# Setup pre-commit hooks
guardian repo hooks install
```

## Security Features

```bash
# Scan repository for sensitive data
guardian security scan .

# Backup configuration
guardian config backup

# Check authentication status
guardian auth status
```

# docs/api/auth.md
# Authentication Service API

The `AuthService` provides comprehensive authentication management functionality.

## Class Reference

```python
class AuthService:
    def setup_ssh(self, email: str, force: bool = False) -> Result:
        """
        Generate and configure SSH keys.
        
        Args:
            email: Email address for the key
            force: Whether to overwrite existing keys
            
        Returns:
            Result object with success status and key path
        """
        pass

    def setup_git_token(self, token: str, name: str = "default") -> Result:
        """
        Store Git authentication token securely.
        
        Args:
            token: The authentication token
            name: Identifier for multiple accounts
            
        Returns:
            Result object with success status
        """
        pass
```

## Planned Features

### Key Rotation
```python
def rotate_keys(self, backup: bool = True) -> Result:
    """
    Automatically rotate SSH and GPG keys.
    
    Args:
        backup: Whether to backup old keys
        
    Returns:
        Result object with new key paths
    """
    pass
```

### Multi-Profile Support
```python
def create_profile(self, name: str, email: str, 
                  token: Optional[str] = None) -> Result:
    """
    Create a new authentication profile.
    
    Args:
        name: Profile name
        email: Associated email
        token: Optional GitHub token
        
    Returns:
        Result object with profile details
    """
    pass
```

# docs/roadmap.md
# Development Roadmap

## Version 1.0 (Current Focus)
- ✅ Basic SSH key management
- ✅ GitHub token storage
- ✅ Repository initialization
- ✅ Security scanning
- 🚧 Documentation
- 🚧 Test coverage

## Version 1.1 (Next Release)
- 🔄 Key rotation automation
- 🔄 Multi-profile support
- 🔄 Enhanced template system
- 🔄 Configuration backup/restore

## Version 1.2 (Planning)
- 📋 Team collaboration features
- 📋 Advanced security scanning
- 📋 CI/CD integration
- 📋 Policy management

## Future Considerations
- Repository analytics
- Custom workflow automation
- Enterprise features
- Cloud integration

# docs/contributing/testing.md
# Testing Guide

## Running Tests

```bash
# Install development dependencies
pip install -e ".[test]"

# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_auth.py

# Run with coverage
pytest --cov=guardian

# Run with verbose output
pytest -v
```

## Writing Tests

### Unit Tests
```python
def test_feature():
    # Arrange
    service = SomeService()
    
    # Act
    result = service.do_something()
    
    # Assert
    assert result.success
    assert result.data['key'] == 'value'
```

### Integration Tests
```python
def test_workflow(auth_service, repo_service):
    # Setup authentication
    auth_result = auth_service.setup_ssh("test@example.com")
    assert auth_result.success
    
    # Initialize repository
    repo_result = repo_service.init("test-repo")
    assert repo_result.success
```

### Test Fixtures
See `tests/conftest.py` for available fixtures:
- `temp_dir`: Clean temporary directory
- `home_dir`: Mocked home directory
- `auth_service`: Fresh AuthService instance
- `repo_service`: Fresh RepoService instance
