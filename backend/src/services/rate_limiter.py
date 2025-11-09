"""Rate limiting service."""

from typing import Dict
from datetime import datetime, timedelta


class RateLimiter:
    """Rate limiter for login and API requests."""

    def __init__(self):
        self.login_attempts: Dict[str, List[datetime]] = {}

    def check_login_attempt(self, ip_address: str, max_attempts: int = 5, window_seconds: int = 300) -> bool:
        """
        Check if IP address exceeds login attempt limit.
        
        Returns True if allowed, False if rate limited.
        """
        now = datetime.utcnow()
        window = timedelta(seconds=window_seconds)

        if ip_address not in self.login_attempts:
            self.login_attempts[ip_address] = []

        # Remove old attempts outside window
        self.login_attempts[ip_address] = [
            t for t in self.login_attempts[ip_address] if now - t < window
        ]

        # Check limit
        if len(self.login_attempts[ip_address]) >= max_attempts:
            return False

        # Record attempt
        self.login_attempts[ip_address].append(now)
        return True


def get_rate_limiter() -> RateLimiter:
    """Get rate limiter instance."""
    return RateLimiter()
