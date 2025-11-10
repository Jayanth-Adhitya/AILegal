"""Rate limit handling with intelligent retry logic."""

import time
import logging
import re
from typing import Callable, Any, Optional
from functools import wraps
from google.api_core import exceptions as google_exceptions

logger = logging.getLogger(__name__)


class RateLimitHandler:
    """Handle API rate limits with exponential backoff and retry logic."""

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 2.0,
        max_delay: float = 60.0
    ):
        """
        Initialize rate limit handler.

        Args:
            max_retries: Maximum number of retry attempts
            base_delay: Base delay in seconds for exponential backoff
            max_delay: Maximum delay between retries
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay

    def extract_retry_delay(self, error: Exception) -> float:
        """
        Extract retry delay from error message.

        Args:
            error: The rate limit exception

        Returns:
            Suggested retry delay in seconds
        """
        error_str = str(error)

        # Look for "retry in X.Xs" or "Please retry in Xs"
        patterns = [
            r'retry in (\d+\.?\d*)\s*s',
            r'Please retry in (\d+\.?\d*)\s*s',
            r'retry_delay.*?seconds:\s*(\d+)'
        ]

        for pattern in patterns:
            match = re.search(pattern, error_str, re.IGNORECASE)
            if match:
                delay = float(match.group(1))
                logger.info(f"Extracted retry delay from error: {delay}s")
                return delay

        # Default to exponential backoff if no delay specified
        return self.base_delay

    def execute_with_retry(
        self,
        api_call: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute API call with automatic retry on rate limit.

        Args:
            api_call: Function to call
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function

        Returns:
            Result of the API call

        Raises:
            Exception: If max retries exceeded
        """
        last_error = None

        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Attempt {attempt + 1}/{self.max_retries}")
                result = api_call(*args, **kwargs)

                if attempt > 0:
                    logger.info(f"✅ Succeeded after {attempt + 1} attempts")

                return result

            except google_exceptions.ResourceExhausted as e:
                last_error = e

                if attempt < self.max_retries - 1:
                    # Calculate delay
                    if "retry" in str(e).lower():
                        delay = self.extract_retry_delay(e)
                    else:
                        delay = min(self.base_delay * (2 ** attempt), self.max_delay)

                    logger.warning(
                        f"⏳ Rate limit hit (attempt {attempt + 1}/{self.max_retries}). "
                        f"Waiting {delay:.1f}s before retry..."
                    )
                    time.sleep(delay)
                else:
                    logger.error(f"❌ Rate limit exceeded after {self.max_retries} attempts")

            except Exception as e:
                # Non-rate-limit errors should fail immediately
                logger.error(f"Non-rate-limit error: {type(e).__name__}: {e}")
                raise

        # If we get here, all retries failed
        raise Exception(
            f"Rate limit exceeded after {self.max_retries} attempts. "
            f"Last error: {last_error}"
        )

    def with_retry(self, func: Callable) -> Callable:
        """
        Decorator to add retry logic to a function.

        Usage:
            @rate_limiter.with_retry
            def my_api_call():
                return llm.invoke(prompt)
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            return self.execute_with_retry(func, *args, **kwargs)

        return wrapper


class BatchRateLimiter:
    """Smart rate limiter for batch operations."""

    def __init__(
        self,
        requests_per_minute: int = 15,
        requests_per_day: int = 250
    ):
        """
        Initialize batch rate limiter.

        Args:
            requests_per_minute: RPM limit
            requests_per_day: Daily quota limit
        """
        self.rpm_limit = requests_per_minute
        self.daily_limit = requests_per_day
        self.request_times = []
        self.daily_count = 0
        self.daily_reset_time = time.time() + 86400  # 24 hours

    def check_and_wait(self):
        """Check rate limits and wait if necessary."""
        current_time = time.time()

        # Reset daily counter if needed
        if current_time > self.daily_reset_time:
            self.daily_count = 0
            self.daily_reset_time = current_time + 86400
            logger.info("🔄 Daily quota reset")

        # Check daily limit
        if self.daily_count >= self.daily_limit:
            wait_time = self.daily_reset_time - current_time
            logger.warning(
                f"⚠️ Daily quota reached ({self.daily_count}/{self.daily_limit}). "
                f"Reset in {wait_time/3600:.1f} hours"
            )
            raise Exception(f"Daily quota exceeded. Resets in {wait_time/3600:.1f} hours")

        # Clean old request times (older than 1 minute)
        self.request_times = [
            t for t in self.request_times
            if current_time - t < 60
        ]

        # Check RPM limit
        if len(self.request_times) >= self.rpm_limit:
            oldest_request = self.request_times[0]
            wait_time = 60 - (current_time - oldest_request)

            if wait_time > 0:
                logger.info(f"⏳ RPM limit reached. Waiting {wait_time:.1f}s")
                time.sleep(wait_time)

        # Record this request
        self.request_times.append(current_time)
        self.daily_count += 1

        logger.debug(
            f"📊 Usage: {len(self.request_times)} req/min, "
            f"{self.daily_count}/{self.daily_limit} today"
        )

    def execute_with_limit(self, api_call: Callable, *args, **kwargs) -> Any:
        """
        Execute API call respecting rate limits.

        Args:
            api_call: Function to call
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Result of API call
        """
        self.check_and_wait()
        return api_call(*args, **kwargs)
