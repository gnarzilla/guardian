# Guardian

```
    ██████╗ ██╗   ██╗ █████╗ ██████╗ ██████╗ ██╗ █████╗ ███╗   ██╗
    ██╔════╝ ██║   ██║██╔══██╗██╔══██╗██╔══██╗██║██╔══██╗████╗  ██║
    ██║  ███╗██║   ██║███████║██████╔╝██║  ██║██║███████║██╔██╗ ██║
    ██║   ██║██║   ██║██╔══██║██╔══██╗██║  ██║██║██╔══██║██║╚██╗██║
    ╚██████╔╝╚██████╔╝██║  ██║██║  ██║██████╔╝██║██║  ██║██║ ╚████║
    ╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝
```

[![PyPI version](https://badge.fury.io/py/guardian-git.svg)](https://badge.fury.io/py/guardian-git)
[![CI Status](https://github.com/yourusername/guardian/workflows/CI/badge.svg)](https://github.com/yourusername/guardian/actions)
[![Documentation Status](https://readthedocs.org/projects/guardian-git/badge/?version=latest)](https://guardian-git.readthedocs.io/en/latest/?badge=latest)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Git User Authentication & Repository Development Interface Assistant & Navigator

## Features

🔒 **Secure Authentication Management**
- SSH key generation and management
- Personal Access Token secure storage
- GitHub CLI credential management
- System keyring integration

🧩 **Configuration Management**
- Git config backup and restore
- SSH key backup with encryption
- Automated config migration

🧪 **Code Quality Tools**
- Pre-commit hook automation
- Code formatting with black
- Import sorting with isort
- Type checking with mypy

📊 **Security Features**
- Audit logging for auth events
- Key rotation management
- Configurable security levels
- Encrypted backup storage

## Installation

### Via pip (recommended)
```bash
pip install guardian-git
```

### From source
```bash
git clone https://github.com/yourusername/guardian.git
cd guardian
pip install -e ".[dev]"
```

## Quick Start

### Authentication Setup
```bash
# Initialize Guardian
guardian init

# Setup SSH authentication
guardian auth setup-ssh

# Configure GitHub tokens
guardian auth setup-github
```

### Code Quality Tools
```bash
# Install pre-commit hooks
guardian hooks install

# Format code
guardian format .

# Run all checks
guardian check
```

### Configuration Management
```bash
# Backup current configuration
guardian backup create

# Restore from backup
guardian backup restore <backup-name>

# Rotate SSH keys
guardian auth rotate-keys
```

## CLI Reference

### Main Commands
- `guardian init`: Initialize Guardian in current directory
- `guardian auth`: Authentication management commands
- `guardian format`: Code formatting commands
- `guardian hooks`: Pre-commit hook management
- `guardian backup`: Configuration backup commands
- `guardian check`: Run all configured checks

### Command Groups
```
guardian/
├── auth/
│   ├── setup-ssh      # SSH key setup
│   ├── setup-github   # GitHub token setup
│   └── rotate-keys    # Key rotation
├── format/
│   ├── run           # Run formatters
│   └── check         # Check formatting
└── hooks/
    ├── install       # Install pre-commit hooks
    └── update        # Update hook configurations
```

## Configuration

Guardian can be configured via `guardian.yaml` in your project root:

```yaml
security:
  level: enhanced  # basic, enhanced, or paranoid
  backup_encryption: true
  audit_logging: true

formatting:
  black_enabled: true
  isort_enabled: true
  mypy_enabled: true

hooks:
  pre_commit:
    - black
    - isort
    - mypy
```

## Contributing

Contributions are welcome! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup
1. Clone the repository
2. Install development dependencies: `pip install -e ".[dev]"`
3. Install pre-commit hooks: `pre-commit install`
4. Run tests: `pytest`

## License

MIT License - see [LICENSE](LICENSE) for details.
