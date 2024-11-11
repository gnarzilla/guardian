# tests/unit/test_security.py
def test_security_scan(security_service, temp_dir):
    """Test security scanning"""
    # Create test file with sensitive data
    test_file = temp_dir / 'test.py'
    test_file.write_text('''
password = "secret123"
aws_key = "AKIAXXXXXXXXXXXXXXXX"
''')
    
    result = security_service.scan_repo(temp_dir)
    assert result.success
    assert len(result.data['findings']) == 2
