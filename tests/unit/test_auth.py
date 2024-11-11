# tests/unit/test_auth.py
def test_ssh_key_generation(auth_service, home_dir):
    """Test SSH key generation"""
    result = auth_service.setup_ssh("test@example.com")
    assert result.success
    assert (home_dir / '.ssh' / 'id_ed25519').exists()
    assert (home_dir / '.ssh' / 'id_ed25519.pub').exists()

def test_ssh_key_exists(auth_service, home_dir):
    """Test SSH key generation when key already exists"""
    # First generation
    auth_service.setup_ssh("test@example.com")
    
    # Second generation without force
    result = auth_service.setup_ssh("test@example.com")
    assert not result.success
    assert "already exists" in result.message

def test_git_token_storage(auth_service):
    """Test Git token storage"""
    result = auth_service.setup_git_token("test-token", "test")
    assert result.success
