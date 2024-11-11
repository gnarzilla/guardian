# src/guardian/core/repo.py
from pathlib import Path
import subprocess
from typing import List, Optional
from guardian.core import Service, Result

class RepoService(Service):
    """Core repository management service"""
    def __init__(self):
        super().__init__()
        self.templates_dir = self.config_dir / 'templates'
        self.templates_dir.mkdir(exist_ok=True)
    
    def init(self, path: Path, template: Optional[str] = None) -> Result:
        """Initialize a new repository with optional template"""
        try:
            path = Path(path).resolve()
            path.mkdir(exist_ok=True)
            
            # Initialize git repository
            subprocess.run(['git', 'init'], cwd=path, check=True)
            
            if template:
                template_path = self.templates_dir / template
                if not template_path.exists():
                    return self.create_result(False, f"Template '{template}' not found")
                
                # Copy template files
                import shutil
                for item in template_path.iterdir():
                    if item.is_file():
                        shutil.copy2(item, path)
                    else:
                        shutil.copytree(item, path / item.name)
            
            return self.create_result(True, "Repository initialized successfully", 
                                    {"path": str(path)})
        except Exception as e:
            return self.create_result(False, "Failed to initialize repository", error=e)
    
    def clone(self, url: str, path: Optional[Path] = None, 
              branch: Optional[str] = None) -> Result:
        """Clone a repository"""
        try:
            cmd = ['git', 'clone']
            if branch:
                cmd.extend(['-b', branch])
            cmd.append(url)
            if path:
                cmd.append(str(path))
            
            subprocess.run(cmd, check=True)
            return self.create_result(True, "Repository cloned successfully")
        except Exception as e:
            return self.create_result(False, "Failed to clone repository", error=e)
    
    def setup_hooks(self, path: Path) -> Result:
        """Setup repository hooks"""
        try:
            hooks_dir = path / '.git' / 'hooks'
            if not hooks_dir.exists():
                return self.create_result(False, "Not a git repository")
            
            # Install pre-commit hook
            pre_commit = hooks_dir / 'pre-commit'
            with open(pre_commit, 'w') as f:
                f.write('''#!/bin/sh
if command -v guardian >/dev/null 2>&1; then
    guardian hooks run pre-commit
else
    echo "Guardian not found, skipping hooks"
fi
''')
            pre_commit.chmod(0o755)
            
            return self.create_result(True, "Hooks setup successfully")
        except Exception as e:
            return self.create_result(False, "Failed to setup hooks", error=e)

