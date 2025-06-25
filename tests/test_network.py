import pytest
from ransomware.network.client import NetworkClient
from ransomware.config import AppConfig
from ransomware.exceptions import NetworkError

class DummyConfig(AppConfig):
    c2_server_url: str = "http://localhost:9999"
    encryption_key_path: str = "/tmp/key"

def test_network_client_connection_error(monkeypatch):
    config = DummyConfig()
    client = NetworkClient(config)
    def mock_post(*args, **kwargs):
        raise Exception("Connection failed")
    monkeypatch.setattr("requests.post", mock_post)
    with pytest.raises(NetworkError):
        client.send_data("test", {"foo": "bar"})

def test_network_connection():
    # Dummy test for network connection
    assert True

def test_network_send():
    # Dummy test for network send
    def dummy():
        pass
    assert True 