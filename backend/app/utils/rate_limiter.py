# Rate limiting utilities
import time
import threading
from typing import Dict, Optional, Any
from collections import defaultdict
from app.core.logging import get_logger
from app.core.exceptions import APIRateLimitException

logger = get_logger(__name__)


class TokenBucket:
    """Token bucket rate limiter implementation."""
    
    def __init__(self, capacity: int, refill_rate: float):
        """
        Initialize token bucket.
        
        Args:
            capacity: Maximum number of tokens
            refill_rate: Tokens added per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()
        self._lock = threading.Lock()
    
    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens from the bucket.
        
        Args:
            tokens: Number of tokens to consume
            
        Returns:
            True if tokens were consumed, False otherwise
        """
        with self._lock:
            self._refill()
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
    
    def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill
        tokens_to_add = elapsed * self.refill_rate
        
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now
    
    def get_wait_time(self, tokens: int = 1) -> float:
        """
        Get time to wait before tokens will be available.
        
        Args:
            tokens: Number of tokens needed
            
        Returns:
            Time in seconds to wait
        """
        with self._lock:
            self._refill()
            
            if self.tokens >= tokens:
                return 0.0
            
            tokens_needed = tokens - self.tokens
            return tokens_needed / self.refill_rate


class RateLimiter:
    """Rate limiter with multiple buckets support."""
    
    def __init__(self):
        self._buckets: Dict[str, TokenBucket] = {}
        self._lock = threading.Lock()
    
    def add_bucket(self, name: str, capacity: int, refill_rate: float) -> None:
        """Add a new rate limit bucket."""
        with self._lock:
            self._buckets[name] = TokenBucket(capacity, refill_rate)
            logger.info(f"Added rate limit bucket '{name}': {capacity} tokens, {refill_rate}/sec")
    
    def consume(self, bucket_name: str, tokens: int = 1) -> bool:
        """
        Try to consume tokens from a bucket.
        
        Args:
            bucket_name: Name of the bucket
            tokens: Number of tokens to consume
            
        Returns:
            True if tokens were consumed, False otherwise
        """
        with self._lock:
            if bucket_name not in self._buckets:
                logger.warning(f"Rate limit bucket '{bucket_name}' not found")
                return True  # Allow if bucket doesn't exist
            
            bucket = self._buckets[bucket_name]
            return bucket.consume(tokens)
    
    def wait_if_needed(self, bucket_name: str, tokens: int = 1) -> None:
        """
        Wait if necessary to respect rate limits.
        
        Args:
            bucket_name: Name of the bucket
            tokens: Number of tokens needed
        """
        with self._lock:
            if bucket_name not in self._buckets:
                return
            
            bucket = self._buckets[bucket_name]
            wait_time = bucket.get_wait_time(tokens)
            
            if wait_time > 0:
                logger.info(f"Rate limit wait: {wait_time:.2f}s for bucket '{bucket_name}'")
                time.sleep(wait_time)
    
    def get_bucket_status(self, bucket_name: str) -> Optional[Dict[str, float]]:
        """Get current status of a bucket."""
        with self._lock:
            if bucket_name not in self._buckets:
                return None
            
            bucket = self._buckets[bucket_name]
            bucket._refill()  # Update tokens
            
            return {
                "tokens": bucket.tokens,
                "capacity": bucket.capacity,
                "refill_rate": bucket.refill_rate,
                "utilization": (bucket.capacity - bucket.tokens) / bucket.capacity
            }


class APIRateLimiter:
    """API-specific rate limiter with retry logic."""
    
    def __init__(self, requests_per_minute: int = 60):
        self.rate_limiter = RateLimiter()
        self.rate_limiter.add_bucket("api", requests_per_minute, requests_per_minute / 60.0)
        self.retry_attempts = 3
        self.retry_delay = 1.0
    
    def execute_with_rate_limit(self, func, *args, **kwargs):
        """
        Execute function with rate limiting and retry logic.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            APIRateLimitException: If rate limit exceeded after retries
        """
        for attempt in range(self.retry_attempts):
            try:
                # Wait if rate limit would be exceeded
                self.rate_limiter.wait_if_needed("api", 1)
                
                # Try to consume token
                if not self.rate_limiter.consume("api", 1):
                    if attempt < self.retry_attempts - 1:
                        wait_time = self.rate_limiter._buckets["api"].get_wait_time(1)
                        logger.warning(f"Rate limit hit, waiting {wait_time:.2f}s (attempt {attempt + 1})")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise APIRateLimitException(
                            retry_after=int(wait_time),
                            details={"attempts": attempt + 1}
                        )
                
                # Execute function
                return func(*args, **kwargs)
                
            except APIRateLimitException:
                if attempt < self.retry_attempts - 1:
                    time.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
                    continue
                else:
                    raise
            except Exception as e:
                logger.error(f"API call failed on attempt {attempt + 1}: {e}")
                if attempt < self.retry_attempts - 1:
                    time.sleep(self.retry_delay)
                    continue
                else:
                    raise
        
        raise APIRateLimitException(
            details={"attempts": self.retry_attempts}
        )
    
    def get_status(self) -> Dict[str, Any]:
        """Get current rate limiter status."""
        status = self.rate_limiter.get_bucket_status("api")
        return {
            "rate_limiter_status": status,
            "retry_attempts": self.retry_attempts,
            "retry_delay": self.retry_delay
        }
