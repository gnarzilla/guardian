# tests/integration/test_workflow.py
def test_complete_workflow(auth_service, config_service, repo_service, temp_dir):
    """Test complete workflow from setup to repository creation"""
    # 1. Setup SSH
    ssh_result = auth_service.setup_ssh("test@example.com")
    assert ssh_result.success
    
    # 2. Setup Git config
    config_result = config_service.setup_git_config(
        name="Test User",
        email="test@example.com"
    )
    assert config_result.success
    
    # 3. Initialize repository
    repo_dir = temp_dir / 'test-project'
    repo_result = repo_service.init(repo_dir)
    assert repo_result.success
    
    # 4. Verify setup
    assert (repo_dir / '.git').exists()
    assert (temp_dir / '.ssh' / 'id_ed25519').exists()
