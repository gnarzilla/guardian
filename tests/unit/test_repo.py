# tests/unit/test_repo.py
def test_repo_init(repo_service, temp_dir):
    """Test repository initialization"""
    target_dir = temp_dir / 'new-repo'
    result = repo_service.init(target_dir)
    assert result.success
    assert (target_dir / '.git').exists()

def test_repo_with_template(repo_service, temp_dir):
    """Test repository initialization with template"""
    # Setup template
    template_dir = temp_dir / '.guardian' / 'templates' / 'python'
    template_dir.mkdir(parents=True)
    (template_dir / 'README.md').write_text('# Test Project')
    
    # Init with template
    target_dir = temp_dir / 'new-repo'
    result = repo_service.init(target_dir, template='python')
    assert result.success
    assert (target_dir / 'README.md').exists()
