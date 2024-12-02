import pytest
from unittest.mock import MagicMock

@pytest.fixture
def mock_email_config():
    return {
        'smtp_server': 'smtp.example.com',
        'smtp_port': 587,
        'sender': 'test@example.com',
        'password': 'test_password'
    }

@pytest.fixture
def mock_smtp(monkeypatch):
    smtp_mock = MagicMock()
    monkeypatch.setattr('smtplib.SMTP', smtp_mock)
    return smtp_mock 