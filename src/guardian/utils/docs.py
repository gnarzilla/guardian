# src/guardian/utils/docs.py
import click
from rich.console import Console
from rich.markdown import Markdown
from pathlib import Path
from typing import Dict, List
import datetime

def generate_feature_list(cli: click.Group) -> str:
    """Generate feature list from CLI commands"""
    features = []
    
    def _process_command(cmd: click.Command, parent: str = ""):
        if isinstance(cmd, click.Group):
            # Add group description
            if cmd.help:
                features.append(f"### {cmd.name.title()}")
                features.append(f"{cmd.help}\n")
            
            # Process subcommands
            for sub_cmd_name, sub_cmd in cmd.commands.items():
                _process_command(sub_cmd, f"{parent} {cmd.name}".strip())
        else:
            # Add command as feature
            command_path = f"{parent} {cmd.name}".strip()
            features.append(f"- `{command_path}`: {cmd.help}")

    _process_command(cli)
    return "\n".join(features)

def generate_changelog_entry(version: str, changes: List[Dict[str, str]]) -> str:
    """Generate a changelog entry"""
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    
    sections = {
        "added": [],
        "changed": [],
        "fixed": [],
    }
    
    for change in changes:
        section = change.get("type", "added").lower()
        if section in sections:
            sections[section].append(change["description"])
    
    lines = [
        f"## [{version}] - {today}\n"
    ]
    
    if sections["added"]:
        lines.append("### Added")
        lines.extend(f"- {item}" for item in sections["added"])
        lines.append("")
        
    if sections["changed"]:
        lines.append("### Changed")
        lines.extend(f"- {item}" for item in sections["changed"])
        lines.append("")
        
    if sections["fixed"]:
        lines.append("### Fixed")
        lines.extend(f"- {item}" for item in sections["fixed"])
        lines.append("")
    
    return "\n".join(lines)

def generate_docs():
    """Generate project documentation"""
    from guardian.cli import cli  # Import your CLI
    docs_dir = Path("docs")
    docs_dir.mkdir(exist_ok=True)
    
    # Generate README.md
    features = generate_feature_list(cli)
    readme_content = f"""# deadlight-guardian

Git Authentication & Development Interface Assistant & Navigator

## Features

{features}

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
pip install deadlight-guardian

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
"""
    
    # Generate CONTRIBUTING.md
    contributing_content = """# Contributing to deadlight-guardian

We love your input! We want to make contributing as easy and transparent as possible.

## Development Process

1. Fork the repo and create your branch from `main`.
2. If you've added code that should be tested, add tests.
3. Update the documentation.
4. Ensure the test suite passes.
5. Make sure your code lints.
6. Issue a pull request.

## Any contributions you make will be under the MIT License
When you submit code changes, your submissions are understood to be under the same [MIT License](LICENSE) that covers the project.

## Report bugs using GitHub's [issue tracker]
We use GitHub issues to track public bugs. Report a bug by [opening a new issue]().

## Write bug reports with detail, background, and sample code

**Great Bug Reports** tend to have:

- A quick summary and/or background
- Steps to reproduce
  - Be specific!
  - Give sample code if you can.
- What you expected would happen
- What actually happens
- Notes (possibly including why you think this might be happening, or stuff you tried that didn't work)

## Development Setup

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the environment: `source venv/bin/activate`
4. Install dependencies: `pip install -e ".[dev]"`
5. Install pre-commit hooks: `guardian hooks install`

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=guardian
```

## Pull Request Process

1. Update the README.md with details of changes if needed.
2. Update the CHANGELOG.md with notes on your changes.
3. The PR will be merged once you have the sign-off of another developer.
"""

    # Write files
    with open("README.md", "w") as f:
        f.write(readme_content)
    
    with open("CONTRIBUTING.md", "w") as f:
        f.write(contributing_content)
    
    # Generate initial CHANGELOG.md
    initial_changes = [
        {"type": "added", "description": "Initial release with core functionality"},
        {"type": "added", "description": "Authentication management (SSH, GitHub)"},
        {"type": "added", "description": "Configuration management"},
        {"type": "added", "description": "Hook management"},
    ]
    
    changelog_content = """# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

"""
    changelog_content += generate_changelog_entry("1.0.0", initial_changes)
    
    with open("CHANGELOG.md", "w") as f:
        f.write(changelog_content)
