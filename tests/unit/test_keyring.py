# tests/unit/test_keyring.py
import pytest
from guardian.services.keyring import KeyringManager

@pytest.fixture
def keyring_manager():
    return KeyringManager(service_name="guardian-test")

def test_store_and_retrieve_credential(keyring_manager):
    """Test storing and retrieving a credential"""
    key = "test-key"
    value = "test-value"
    
    # Store credential
    result = keyring_manager.store_credential(key, value)
    assert result.success
    
    # Retrieve credential
    stored_value = keyring_manager.get_credential(key)
    assert stored_value == value

def test_delete_credential(keyring_manager):
    """Test deleting a credential"""
    key = "test-key"
    value = "test-value"
    
    # Store credential
    keyring_manager.store_credential(key, value)
    
    # Delete credential
    result = keyring_manager.delete_credential(key)
    assert result.success
    
    # Verify deletion
    stored_value = keyring_manager.get_credential(key)
    assert stored_value is None

def test_delete_nonexistent_credential(keyring_manager):
    """Test deleting a credential that doesn't exist"""
    result = keyring_manager.delete_credential("nonexistent")
    assert not result.success
    assert "not found" in result.message

def test_list_credentials(keyring_manager):
    """Test listing credentials"""
    # Store some test credentials
    keyring_manager.store_credential("github_token", "token1")
    keyring_manager.store_credential("gpg_key", "key1")
    
    # List credentials
    result = keyring_manager.list_credentials()
    assert result.success
    assert len(result.data['keys']) >= 2
    assert "github_token" in result.data['keys']
    assert "gpg_key" in result.data['keys']

def test_rotate_credential(keyring_manager):
    """Test credential rotation"""
    key = "test-key"
    old_value = "old-value"
    new_value = "new-value"
    
    # Store initial credential
    keyring_manager.store_credential(key, old_value)
    
    # Rotate credential
    result = keyring_manager.rotate_credential(key, new_value)
    assert result.success
    
    # Verify new value
    stored_value = keyring_manager.get_credential(key)
    assert stored_value == new_value

def test_rotate_nonexistent_credential(keyring_manager):
    """Test rotating a credential that doesn't exist"""
    result = keyring_manager.rotate_credential("nonexistent", "new-value")
    assert not result.success
    assert "not found" in result.message

@pytest.fixture(autouse=True)
def cleanup(keyring_manager):
    """Clean up any credentials after each test"""
    yield
    for key in ['test-key', 'github_token', 'gpg_key']:
        try:
            keyring_manager.delete_credential(key)
        except:
            pass
