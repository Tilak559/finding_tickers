# Simplified unit tests - Essential functionality only
import pytest
from unittest.mock import Mock, patch
from app.services.finnhub_service import FinnhubService
from app.services.enrichment_service import EnrichmentService
from app.core.exceptions import SymbolNotFoundException, APIRateLimitException


class TestFinnhubService:
    """Test FinnhubService essential functionality."""
    
    def test_singleton_pattern(self):
        """Test singleton pattern implementation."""
        service1 = FinnhubService()
        service2 = FinnhubService()
        
        assert service1 is service2
    
    @patch('app.services.finnhub_service.finnhub.Client')
    def test_lookup_symbol_success(self, mock_client_class):
        """Test successful symbol lookup."""
        mock_client = Mock()
        mock_response = {
            "result": [{"symbol": "AAPL", "description": "Apple Inc"}]
        }
        mock_client.symbol_lookup.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        service = FinnhubService()
        service.rate_limiter.execute_with_rate_limit = Mock(return_value=mock_response)
        
        result = service.lookup_symbol("Apple Inc")
        
        assert result == "AAPL"
    
    @patch('app.services.finnhub_service.finnhub.Client')
    def test_lookup_symbol_not_found(self, mock_client_class):
        """Test symbol not found."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        service = FinnhubService()
        service.rate_limiter.execute_with_rate_limit = Mock(return_value={"result": []})
        
        with pytest.raises(SymbolNotFoundException):
            service.lookup_symbol("Unknown Company")
    
    @patch('app.services.finnhub_service.finnhub.Client')
    def test_lookup_symbol_rate_limit(self, mock_client_class):
        """Test rate limit exception."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        service = FinnhubService()
        service.rate_limiter.execute_with_rate_limit = Mock(
            side_effect=APIRateLimitException(retry_after=60)
        )
        
        with pytest.raises(APIRateLimitException):
            service.lookup_symbol("Apple Inc")


class TestEnrichmentService:
    """Test EnrichmentService essential functionality."""
    
    def test_initialization(self):
        """Test service initialization."""
        service = EnrichmentService()
        
        assert service.finnhub_service is not None
        assert service.threads > 0
        assert service.page_size > 0
    
    @patch('app.services.enrichment_service.FinnhubService.lookup_symbol')
    def test_get_symbol_success(self, mock_lookup):
        """Test successful symbol retrieval."""
        mock_lookup.return_value = "AAPL"
        
        service = EnrichmentService()
        result = service.get_symbol("Apple Inc")
        
        assert result == "AAPL"
    
    @patch('app.services.enrichment_service.FinnhubService.lookup_symbol')
    def test_get_symbol_failure(self, mock_lookup):
        """Test symbol retrieval failure."""
        mock_lookup.side_effect = Exception("API Error")
        
        service = EnrichmentService()
        result = service.get_symbol("Unknown Company")
        
        assert result is None
    
    def test_process_row_success(self):
        """Test successful row processing."""
        service = EnrichmentService()
        
        with patch.object(service, 'get_symbol', return_value="AAPL"):
            idx, symbol = service.process_row(0, "Apple Inc")
            
            assert idx == 0
            assert symbol == "AAPL"
    
    def test_process_row_failure(self):
        """Test row processing failure."""
        service = EnrichmentService()
        
        with patch.object(service, 'get_symbol', return_value=None):
            idx, symbol = service.process_row(0, "Unknown Company")
            
            assert idx == 0
            assert symbol is None
    
    def test_process_row_invalid_input(self):
        """Test row processing with invalid input."""
        service = EnrichmentService()
        
        # Test with empty string
        idx, symbol = service.process_row(0, "")
        assert idx == 0
        assert symbol is None
        
        # Test with None
        idx, symbol = service.process_row(0, None)
        assert idx == 0
        assert symbol is None
