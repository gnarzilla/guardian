# deadlight-guardian

Git Authentication & Development Interface Assistant & Navigator

## Features

### Cli
Guardian: Git Authentication & Development Assistant
    
    A comprehensive tool for managing Git authentication, security,
    and development workflows.
    

### Auth
Authentication management commands

- `cli auth setup-github`: Configure GitHub Personal Access Token (PAT) for authentication
- `cli auth setup-ssh`: Generate and configure SSH keys
- `cli auth status`: Check status of all authentication methods
- `cli auth validate-github`: Validate GitHub token and show its capabilities
- `cli auth list`: List configured authentication methods
- `cli auth debug-tokens`: Debug token storage (development only)
- `cli auth debug-service`: Debug auth service configuration
- `cli auth setup-signing`: Setup GPG key for commit signing
### Config
Configuration management commands

- `cli config set`: Set a configuration value
- `cli config get`: Get a configuration value
- `cli config unset`: Remove a configuration value
- `cli config init`: Initialize configuration with defaults
### Hooks
Pre-commit hook management

- `cli hooks templates`: List available hook templates
- `cli hooks install`: Install Git hooks using specified template
- `cli hooks list`: List installed hooks and their status
- `cli hooks show`: Show content of an installed hook
- `cli hooks remove`: Remove an installed hook
### Format
Code formatting commands

- `cli format run`: Format code using configured formatters
- `cli format configure`: Configure formatting settings
- `cli init`: Initialize Guardian in the current directory
### Repo
Repository and remote management commands

- `cli repo create`: Create a remote repository for the current project
- `cli repo connect`: Connect existing repository to a remote
- `cli repo sync`: Synchronize repository configuration across systems
- `cli repo apply-sync`: Apply synchronized configuration from .guardian-sync.yml

## Installation

```bash
pip install deadlight-guardian
```

## Quick Start

```bash
# Initialize Guardian
guardian init

# Setup authentication
guardian auth setup-ssh
guardian auth setup-github

# Check status
guardian auth status
```

## Usage Examples

Here are some common use cases:

### Setting up a new machine
```bash
# Install Guardian
pip install guardian

# Setup authentication
guardian auth setup-ssh
guardian auth setup-github

# Verify setup
guardian auth status
```

### Managing Git configurations
```bash
# View current configuration
guardian config get

# Set configuration
guardian config set user.name "Your Name"
guardian config set user.email "your@email.com"
```

### Working with hooks
```bash
# Install hooks
guardian hooks install

# View installed hooks
guardian hooks list
```

For more examples and detailed documentation, visit our [documentation site](docs/).

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## License

MIT License - see [LICENSE](LICENSE) for details.
