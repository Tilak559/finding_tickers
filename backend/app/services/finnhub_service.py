# Finnhub API service
import finnhub
import time
from typing import Optional, Dict, Any, List
from app.core.config import settings
from app.core.logging import get_logger
from app.core.exceptions import (
    SymbolNotFoundException,
    APIRateLimitException,
    ServiceUnavailableException,
    ValidationException
)
from app.utils.rate_limiter import APIRateLimiter
from app.utils.matcher import NLPMatcher

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
            # For symbol_lookup, log the response structure for debugging
            if method_name == "symbol_lookup" and isinstance(response, dict):
                logger.debug(f"Symbol lookup response keys: {list(response.keys())}")
                if "result" in response and response["result"]:
                    logger.debug(f"First result sample: {response['result'][0]}")
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
    
    def lookup_symbol(self, company_name: str) -> tuple[Optional[str], Optional[str]]:
        """
        Look up stock symbol and description for a company with NLP-based retry logic.
        
        This method tries up to 3 times:
        1. First attempt: Uses the original first word from company name
        2. If it fails: Uses NLP to suggest correction and retries
        3. Final attempt: Tries with NLP correction if different from first attempt
        
        Args:
            company_name: Company name to lookup
            
        Returns:
            Tuple of (stock_symbol, description) if found, (None, None) otherwise
            
        Raises:
            SymbolNotFoundException: If symbol not found after all attempts
            APIRateLimitException: If rate limit exceeded
        """
        # Clean and validate company name
        company_name = company_name.strip()
        if not company_name:
            raise ValidationException(
                field="company_name",
                value=company_name,
                reason="Company name cannot be empty"
            )
        
        # Extract first word (original logic)
        original_symbol = company_name.split(" ")[0]
        
        # Try up to 3 times
        max_attempts = 3
        attempts = []
        search_word = original_symbol  # Initialize with original word
        
        for attempt_num in range(1, max_attempts + 1):
            try:
                # Determine which word to use for this attempt
                if attempt_num == 1:
                    # First attempt: use original word
                    search_word = original_symbol
                    logger.info(f"Attempt {attempt_num}/{max_attempts}: Trying original word '{search_word}' for company '{company_name}'")
                else:
                    # Subsequent attempts: use NLP correction
                    corrected_word = NLPMatcher.get_corrected_word(original_symbol)
                    if corrected_word and corrected_word.lower() != original_symbol.lower():
                        search_word = corrected_word
                        logger.info(f"Attempt {attempt_num}/{max_attempts}: Trying NLP-corrected word '{search_word}' (from '{original_symbol}') for company '{company_name}'")
                    else:
                        # No good correction found, skip this attempt
                        logger.warning(f"Attempt {attempt_num}/{max_attempts}: No NLP correction found for '{original_symbol}', skipping")
                        if attempt_num == max_attempts:
                            # Last attempt failed, raise exception
                            raise SymbolNotFoundException(
                                company_name,
                                details={
                                    "attempts": attempts,
                                    "original_word": original_symbol,
                                    "nlp_available": corrected_word is not None
                                }
                            )
                        continue
                
                # Make API call
                attempts.append({"attempt": attempt_num, "word": search_word, "status": "tried"})
                response = self._make_api_call("symbol_lookup", search_word)
                logger.info(f"API response for '{search_word}': {response}")
                
                # Check if we got results
                if "result" in response and response["result"]:
                    first_result = response["result"][0]
                    logger.info(f"First result keys: {list(first_result.keys())}")
                    logger.info(f"First result data: {first_result}")
                    found_symbol = first_result.get("symbol")
                    # Extract description - check multiple possible keys
                    found_description = (
                        first_result.get("description") or 
                        first_result.get("displaySymbol") or 
                        first_result.get("name") or 
                        ""
                    )
                    # Convert to string and strip whitespace
                    if found_description:
                        found_description = str(found_description).strip()
                    else:
                        found_description = ""
                    logger.info(f"Extracted symbol: '{found_symbol}', description: '{found_description}' (type: {type(found_description)})")
                    attempts[-1]["status"] = "success"
                    logger.info(f"Symbol found on attempt {attempt_num} for '{search_word}': {found_symbol}, description: '{found_description}'")
                    return found_symbol, found_description
                else:
                    # No results, log and continue to next attempt
                    attempts[-1]["status"] = "no_results"
                    logger.warning(f"Attempt {attempt_num}/{max_attempts}: No results found for '{search_word}'")
                    if attempt_num == max_attempts:
                        # Last attempt failed
                        raise SymbolNotFoundException(
                            company_name,
                            details={
                                "attempts": attempts,
                                "original_word": original_symbol,
                                "last_searched_word": search_word
                            }
                        )
                    continue
                    
            except APIRateLimitException:
                # Rate limit - don't retry, raise immediately
                logger.error(f"Rate limit exceeded during attempt {attempt_num} for '{company_name}'")
                raise
            except SymbolNotFoundException as e:
                # If it's the last attempt, re-raise it
                if attempt_num == max_attempts:
                    e.details = e.details or {}
                    e.details["attempts"] = attempts
                    raise
                # Otherwise continue to next attempt
                logger.warning(f"Attempt {attempt_num} failed for '{company_name}', trying next attempt...")
                continue
            except Exception as e:
                # Unexpected error - log and continue if not last attempt
                logger.error(f"Unexpected error on attempt {attempt_num} for '{company_name}': {e}")
                attempts.append({"attempt": attempt_num, "word": search_word, "status": "error", "error": str(e)})
                if attempt_num == max_attempts:
                    raise SymbolNotFoundException(
                        company_name,
                        details={
                            "error": str(e),
                            "attempts": attempts,
                            "original_word": original_symbol
                        }
                    )
                continue
        
        # Should never reach here, but just in case
        raise SymbolNotFoundException(
            company_name,
            details={
                "attempts": attempts,
                "original_word": original_symbol
            }
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
                symbol, _ = self.lookup_symbol(company_name)
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
