# conftest.py
import pytest

@pytest.fixture
def client(test_client):
    """Alias para test_client para mantener compatibilidad"""
    return test_client