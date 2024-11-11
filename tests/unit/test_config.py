# tests/unit/test_config.py
def test_config_storage(config_service):
    """Test configuration storage and retrieval"""
    result = config_service.set("test.key", "test-value")
    assert result.success
    
    value = config_service.get("test.key")
    assert value == "test-value"

def test_git_config_setup(config_service):
    """Test Git configuration setup"""
    result = config_service.setup_git_config(
        name="Test User",
        email="test@example.com"
    )
    assert result.success
