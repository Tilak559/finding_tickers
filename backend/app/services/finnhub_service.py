# Finnhub API service
import finnhub
import time
from typing import Optional, Dict, Any, List
from app.core.config import settings
from app.core.logging import get_logger
from app.core.exceptions import (
    SymbolNotFoundException,
    APIRateLimitException,
    ServiceUnavailableException
)
from app.utils.rate_limiter import APIRateLimiter

logger = get_logger(__name__)


class FinnhubService:
    """Service for interacting with Finnhub API."""
    
    _instance = None
    _client = None
    
    def __new__(cls):
        """Singleton pattern implementation."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize Finnhub client."""
        if self._client is None:
            try:
                self._client = finnhub.Client(api_key=settings.finnhub_api_key)
                self.rate_limiter = APIRateLimiter(settings.rate_limit_per_minute)
                logger.info("Finnhub client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Finnhub client: {e}")
                raise ServiceUnavailableException(
                    service="finnhub",
                    reason=f"Client initialization failed: {str(e)}"
                )

    def _make_api_call(self, method_name: str, *args, **kwargs) -> Dict[str, Any]:
        """
        Make API call with rate limiting and error handling.
        
        Args:
            method_name: Name of the Finnhub client method
            *args: Method arguments
            **kwargs: Method keyword arguments
            
        Returns:
            API response data
            
        Raises:
            APIRateLimitException: If rate limit exceeded
            ServiceUnavailableException: If service is unavailable
        """
        try:
            def api_call():
                method = getattr(self._client, method_name)
                return method(*args, **kwargs)
            
            # Execute with rate limiting
            response = self.rate_limiter.execute_with_rate_limit(api_call)
            
            logger.debug(f"Finnhub API call '{method_name}' successful")
            return response
            
        except APIRateLimitException as e:
            logger.warning(f"Finnhub API rate limit exceeded: {e.message}")
            raise
        except Exception as e:
            logger.error(f"Finnhub API call '{method_name}' failed: {e}")
            raise ServiceUnavailableException(
                service="finnhub",
                reason=f"API call failed: {str(e)}"
            )
    
    def lookup_symbol(self, company_name: str) -> Optional[str]:
        """
        Look up stock symbol for a company.
        
        Args:
            company_name: Company name to lookup
            
        Returns:
            Stock symbol if found, None otherwise
            
        Raises:
            SymbolNotFoundException: If symbol not found
            APIRateLimitException: If rate limit exceeded
        """
        try:
            # Clean and validate company name
            company_name = company_name.strip()
            if not company_name:
                raise ValidationException("Company name cannot be empty")
            
            # Use original logic: symbol can't be too long so we are trimming after the 1st word
            symbol = company_name.split(" ")[0]
            
            logger.info(f"After trimming Symbol: {symbol}")
            response = self._make_api_call("symbol_lookup", symbol)
            logger.info(f"Data: {response}")
            
            if "result" in response and response["result"]:
                found_symbol = response["result"][0]["symbol"]
                logger.info(f"Company profile found for {symbol}: {found_symbol}")
                return found_symbol
            else:
                logger.error(f"No data found for {symbol}")
                raise SymbolNotFoundException(company_name)
            
        except SymbolNotFoundException:
            raise
        except APIRateLimitException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error looking up symbol for '{company_name}': {e}")
            raise SymbolNotFoundException(
                company_name,
                details={"error": str(e)}
            )
    
    def lookup_multiple_symbols(self, company_names: List[str]) -> Dict[str, Optional[str]]:
        """
        Look up symbols for multiple companies.
        
        Args:
            company_names: List of company names
            
        Returns:
            Dictionary mapping company names to symbols
        """
        results = {}
        
        for company_name in company_names:
            try:
                symbol = self.lookup_symbol(company_name)
                results[company_name] = symbol
            except SymbolNotFoundException:
                results[company_name] = None
                logger.warning(f"No symbol found for: {company_name}")
            except APIRateLimitException as e:
                logger.error(f"Rate limit exceeded for: {company_name}")
                results[company_name] = None
                # Add delay before continuing
                time.sleep(e.details.get("retry_after", 60))
            except Exception as e:
                logger.error(f"Error looking up symbol for '{company_name}': {e}")
                results[company_name] = None
        
        return results
    
    def get_company_profile(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get company profile information.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Company profile data
        """
        try:
            response = self._make_api_call("company_profile2", symbol=symbol)
            
            if response and "name" in response:
                logger.info(f"Company profile retrieved for symbol: {symbol}")
                return response
            else:
                logger.warning(f"No company profile found for symbol: {symbol}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting company profile for '{symbol}': {e}")
            return None
    
    def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get real-time quote for a symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Quote data
        """
        try:
            response = self._make_api_call("quote", symbol)
            
            if response and "c" in response:  # 'c' is current price
                logger.info(f"Quote retrieved for symbol: {symbol}")
                return response
            else:
                logger.warning(f"No quote found for symbol: {symbol}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting quote for '{symbol}': {e}")
            return None
    
    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get current rate limit status."""
        return self.rate_limiter.get_status()
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on Finnhub service.
        
        Returns:
            Health status information
        """
        try:
            # Try a simple API call
            response = self._make_api_call("symbol_lookup", "AAPL")
            
            return {
                "status": "healthy",
                "rate_limit_status": self.get_rate_limit_status(),
                "api_accessible": True
            }
            
        except Exception as e:
            logger.error(f"Finnhub health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "api_accessible": False
            }
