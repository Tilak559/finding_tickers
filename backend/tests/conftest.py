# Test configuration and utilities
import os
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import Settings


@pytest.fixture
def test_settings():
    """Test settings with temporary values."""
    return Settings(
        finnhub_api_key="test_api_key",
        api_timeout=5,
        api_max_retries=1,
        max_workers=2,
        page_size=10,
        rate_limit_per_minute=10,
        max_file_size_mb=1,
        allowed_extensions=[".csv"],
        upload_dir=Path("test_data"),
        log_level="DEBUG",
        debug=True
    )


@pytest.fixture
def temp_dir():
    """Create temporary directory for tests."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_csv_data():
    """Sample CSV data for testing."""
    return """Name,Symbol
Apple Inc,
Microsoft Corporation,
Google LLC,
Tesla Inc,
Amazon.com Inc,"""


@pytest.fixture
def sample_csv_file(temp_dir, sample_csv_data):
    """Create sample CSV file for testing."""
    csv_path = temp_dir / "test_companies.csv"
    csv_path.write_text(sample_csv_data)
    return csv_path


@pytest.fixture
def mock_finnhub_response():
    """Mock Finnhub API response."""
    return {
        "result": [
            {
                "symbol": "AAPL",
                "description": "Apple Inc",
                "type": "Common Stock"
            }
        ]
    }


@pytest.fixture
def mock_finnhub_client(mock_finnhub_response):
    """Mock Finnhub client."""
    mock_client = Mock()
    mock_client.symbol_lookup.return_value = mock_finnhub_response
    return mock_client


@pytest.fixture
def test_client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def mock_upload_file():
    """Mock uploaded file."""
    mock_file = Mock()
    mock_file.filename = "test.csv"
    mock_file.content_type = "text/csv"
    mock_file.file = Mock()
    mock_file.file.read.return_value = b"Name,Symbol\nApple Inc,\nMicrosoft Corporation,"
    return mock_file


class TestBase:
    """Base test class with common utilities."""
    
    @staticmethod
    def create_temp_csv(content: str, temp_dir: Path) -> Path:
        """Create temporary CSV file."""
        csv_path = temp_dir / "test.csv"
        csv_path.write_text(content)
        return csv_path
    
    @staticmethod
    def assert_valid_response(response, expected_status: int = 200):
        """Assert valid API response."""
        assert response.status_code == expected_status
        assert "request_id" in response.headers or response.status_code >= 400
    
    @staticmethod
    def assert_error_response(response, expected_status: int, error_field: str = "error"):
        """Assert error response format."""
        assert response.status_code == expected_status
        data = response.json()
        assert error_field in data
        assert "request_id" in data
        assert "timestamp" in data


@pytest.fixture(autouse=True)
def setup_test_env():
    """Setup test environment."""
    # Set test environment variables
    os.environ["FINNHUB_API_KEY"] = "test_key"
    os.environ["LOG_LEVEL"] = "DEBUG"
    os.environ["DEBUG"] = "true"
    
    yield
    
    # Cleanup
    for key in ["FINNHUB_API_KEY", "LOG_LEVEL", "DEBUG"]:
        if key in os.environ:
            del os.environ[key]
