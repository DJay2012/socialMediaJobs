"""
API Keys Manager
Manages multiple API keys with automatic rotation and error handling
"""

import random
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from dotenv import load_dotenv
from src.log.logging import logger
import os

load_dotenv()


# Load API keys from environment variables for security
YOUTUBE_API_KEYS = [
    os.getenv("YOUTUBE_API_KEY_1"),
    os.getenv("YOUTUBE_API_KEY_2"),
    # os.getenv("YOUTUBE_API_KEY_3"), Deactivated
    os.getenv("YOUTUBE_API_KEY_4"),
    os.getenv("YOUTUBE_API_KEY_5"),
    os.getenv("YOUTUBE_API_KEY_6"),
    os.getenv("YOUTUBE_API_KEY_7"),
    os.getenv("YOUTUBE_API_KEY_8"),
    os.getenv("YOUTUBE_API_KEY_9"),
    os.getenv("YOUTUBE_API_KEY_10"),
]

TWITTER_BEARER_TOKENS = [os.getenv("TWITTER_BEARER_TOKEN")]

APIFY_API_TOKENS = [os.getenv("APIFY_API_TOKEN")]

Youtube = "youtube"
Twitter = "twitter"
Apify = "apify"

Services = [Youtube, Twitter, Apify]


@dataclass
class APIKeyInfo:
    """Information about an API key"""

    key: str
    name: str
    last_used: Optional[datetime] = None
    error_count: int = 0
    is_active: bool = True
    quota_reset_time: Optional[datetime] = None


class CredentialManager:
    """Manages multiple API keys with automatic rotation"""

    def __init__(self):
        self.logger = logger
        self.keys: Dict[str, List[APIKeyInfo]] = {service: [] for service in Services}
        self.current_key_index: Dict[str, int] = {service: 0 for service in Services}
        self._load_api_keys()

    def _load_api_keys(self):
        """Load API keys from environment variables"""

        for i, key in enumerate(YOUTUBE_API_KEYS):
            if key and not key.startswith("your_"):
                self.keys[Youtube].append(
                    APIKeyInfo(key=key, name=f"YouTube_API_{i+1}", is_active=True)
                )

        for i, token in enumerate(TWITTER_BEARER_TOKENS):
            if token and not token.startswith("your_"):
                self.keys[Twitter].append(
                    APIKeyInfo(key=token, name=f"Twitter_API_{i+1}", is_active=True)
                )

        for i, token in enumerate(APIFY_API_TOKENS):
            if token and not token.startswith("your_"):
                self.keys[Apify].append(
                    APIKeyInfo(key=token, name=f"Apify_API_{i+1}", is_active=True)
                )

        self.logger.info(
            f"Loaded {len(self.keys[Youtube])} YouTube keys, "
            f"{len(self.keys[Twitter])} Twitter keys, "
            f"{len(self.keys[Apify])} Apify keys"
        )

    def _validate_key(
        self, service: str, active_keys: List[APIKeyInfo], test_func=None
    ) -> Optional[str]:
        for key_info in active_keys:
            if test_func and not test_func(key_info.key):
                continue
            return key_info.key

        self.logger.error(f"No working API keys found for service: {service}")
        return None

    def _get_round_robin_key(self, service: str, active_keys: List[APIKeyInfo]) -> str:
        """Get next key in round-robin fashion"""
        if not active_keys:
            return None

        current_index = self.current_key_index[service] % len(active_keys)
        selected_key = active_keys[current_index]

        # Update last used time
        selected_key.last_used = datetime.now()

        # Move to next key for next call
        self.current_key_index[service] = (current_index + 1) % len(active_keys)

        self.logger.debug(f"Using {selected_key.name} for {service}")
        return selected_key.key

    def _get_random_key(self, active_keys: List[APIKeyInfo]) -> str:
        """Get a random key from active keys"""
        selected_key = random.choice(active_keys)
        selected_key.last_used = datetime.now()
        self.logger.debug(f"Using random key {selected_key.name}")
        return selected_key.key

    def _get_least_used_key(self, active_keys: List[APIKeyInfo]) -> str:
        """Get the least recently used key"""
        selected_key = min(active_keys, key=lambda k: k.last_used or datetime.min)
        selected_key.last_used = datetime.now()
        self.logger.debug(f"Using least used key {selected_key.name}")
        return selected_key.key

    def report_error(
        self, service: str, api_key: str, error_type: str = "quota_exceeded"
    ):
        """Report an error with a specific API key"""
        for key_info in self.keys[service]:
            if key_info.key == api_key:
                key_info.error_count += 1

                if error_type == "quota_exceeded":
                    # Set quota reset time (typically 24 hours for YouTube)
                    key_info.quota_reset_time = datetime.now() + timedelta(hours=24)
                    key_info.is_active = False
                    self.logger.warning(
                        f"Key {key_info.name} quota exceeded, deactivated until {key_info.quota_reset_time}"
                    )
                elif error_type == "invalid_key":
                    key_info.is_active = False
                    self.logger.error(f"Key {key_info.name} is invalid, deactivated")
                elif error_type == "rate_limit":
                    # Temporary deactivation for rate limiting
                    key_info.quota_reset_time = datetime.now() + timedelta(minutes=15)
                    key_info.is_active = False
                    self.logger.warning(
                        f"Key {key_info.name} rate limited, deactivated for 15 minutes"
                    )

                break

    def reactivate_keys(self):
        """Check if any deactivated keys can be reactivated"""
        now = datetime.now()

        for service in self.keys:
            for key_info in self.keys[service]:
                if not key_info.is_active and key_info.quota_reset_time:
                    if now >= key_info.quota_reset_time:
                        key_info.is_active = True
                        key_info.quota_reset_time = None
                        key_info.error_count = 0
                        self.logger.info(
                            f"Reactivated key {key_info.name} for {service}"
                        )

    def get_key_status(self, service: str) -> Dict:
        """Get status of all keys for a service"""
        status = {
            "total_keys": len(self.keys[service]),
            "active_keys": len([k for k in self.keys[service] if k.is_active]),
            "inactive_keys": len([k for k in self.keys[service] if not k.is_active]),
            "keys": [],
        }

        for key_info in self.keys[service]:
            status["keys"].append(
                {
                    "name": key_info.name,
                    "is_active": key_info.is_active,
                    "error_count": key_info.error_count,
                    "last_used": (
                        key_info.last_used.isoformat() if key_info.last_used else None
                    ),
                    "quota_reset_time": (
                        key_info.quota_reset_time.isoformat()
                        if key_info.quota_reset_time
                        else None
                    ),
                }
            )

        return status

    def get_api_keys(self, service: str) -> List[str]:
        """Get all API keys for a service"""
        return [key.key for key in self.keys[service]]

    def get_api_key(
        self, service: str, strategy: str = "round_robin", test_func=None
    ) -> Optional[str]:

        if service not in self.keys or not self.keys[service]:
            self.logger.error(f"No API keys available for service: {service}")
            return None

        active_keys = [key for key in self.keys[service] if key.is_active]
        if not active_keys:
            self.logger.error(f"No active API keys available for service: {service}")
            return None

        if test_func:
            key = self._validate_key(service, active_keys, test_func)
            if key:
                return key

        if strategy == "round_robin":
            return self._get_round_robin_key(service, active_keys)
        elif strategy == "random":
            return self._get_random_key(active_keys)
        elif strategy == "least_used":
            return self._get_least_used_key(active_keys)
        else:
            return self._get_round_robin_key(service, active_keys)

    def add_api_key(self, service: str, key: str, name: str = None):
        """Add a new API key for a service"""
        if service not in self.keys:
            self.keys[service] = []

        key_name = name or f"{service}_API_{len(self.keys[service]) + 1}"
        self.keys[service].append(APIKeyInfo(key=key, name=key_name, is_active=True))

        self.logger.info(f"Added new API key {key_name} for {service}")

    def remove_api_key(self, service: str, key: str):
        """Remove an API key for a service"""
        if service not in self.keys:
            return False

        for i, key_info in enumerate(self.keys[service]):
            if key_info.key == key:
                removed_key = self.keys[service].pop(i)
                self.logger.info(f"Removed API key {removed_key.name} for {service}")
                return True

        return False


# Global instance
credential_manager = CredentialManager()
