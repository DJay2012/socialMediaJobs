import json
import os
import time
import sys
from datetime import datetime, timedelta
from typing import Any, Optional, Dict
from threading import Lock
from src.log.logging import logger

# Platform-specific file locking
if sys.platform == "win32":
    import msvcrt

    def lock_file(file_handle, exclusive=True):
        """Lock file on Windows

        Args:
            file_handle: File handle to lock
            exclusive: If True, acquire exclusive lock (for writing), else shared lock (for reading)
        """
        try:
            # Lock the entire file (use a large number for byte count)
            # Note: For exclusive locks on Windows, file must be opened in a mode that allows writing
            if exclusive:
                # Exclusive lock (write mode) - non-blocking
                msvcrt.locking(file_handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                # For read operations, use non-blocking lock
                msvcrt.locking(file_handle.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            # If lock fails, try blocking lock as fallback
            msvcrt.locking(file_handle.fileno(), msvcrt.LK_LOCK, 1)

    def unlock_file(file_handle):
        """Unlock file on Windows"""
        try:
            msvcrt.locking(file_handle.fileno(), msvcrt.LK_UNLCK, 1)
        except OSError:
            # File might already be unlocked
            pass

else:
    import fcntl

    def lock_file(file_handle, exclusive=True):
        """Lock file on Unix/Linux

        Args:
            file_handle: File handle to lock
            exclusive: If True, acquire exclusive lock, else shared lock
        """
        if exclusive:
            fcntl.flock(file_handle.fileno(), fcntl.LOCK_EX)
        else:
            fcntl.flock(file_handle.fileno(), fcntl.LOCK_SH)

    def unlock_file(file_handle):
        """Unlock file on Unix/Linux"""
        fcntl.flock(file_handle.fileno(), fcntl.LOCK_UN)


class Cache:
    """
    A simple file-based cache utility that stores key-value pairs in a JSON file.

    Features:
    - Stores data with configurable TTL (default: 24 hours)
    - Thread-safe operations
    - Automatic cleanup of expired entries
    - Statistics and monitoring

    Usage:
        cache = Cache(cache_file='cache.json')
        cache.set('key', 'value')
        value = cache.get('key')
        stats = cache.stats()
    """

    def __init__(
        self,
        cache_file: str = "temp/cache.json",
        default_ttl: int = 86400,
        auto_cleanup: bool = True,
        allow_falsy: bool = False,
    ):
        """
        Initialize the Cache instance.

        Args:
            cache_file (str): Path to the JSON file for storing cache data
            default_ttl (int): Default time-to-live in seconds (default: 86400 = 24 hours)
            auto_cleanup (bool): Automatically cleanup expired entries on operations
            allow_falsy (bool): Allow falsy values (None, False, 0, "", [], {}) to be cached (default: False)
        """
        self.cache_file = cache_file
        self.default_ttl = default_ttl
        self.auto_cleanup = auto_cleanup
        self.allow_falsy = allow_falsy
        self._lock = Lock()
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._load()

        if self.auto_cleanup:
            self.cleanup()

    def _load_without_lock(self) -> None:
        """Load cache data from JSON file without acquiring lock (internal use)."""
        if os.path.exists(self.cache_file):
            try:
                # On Windows, avoid locking for read operations to prevent permission errors
                # Simple read without file locking - the thread lock is sufficient for our use case
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    # Handle empty file
                    if not content:
                        self._cache = {}
                    else:
                        self._cache = json.loads(content)
            except PermissionError as e:
                logger.warning(
                    f"Permission denied reading cache file '{self.cache_file}': {e}. "
                    f"Check file permissions. Using existing cache state."
                )
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(
                    f"Error loading cache file: {e}. Using existing cache state."
                )
        else:
            self._cache = {}

    def _load(self) -> None:
        """Load cache data from JSON file."""
        with self._lock:
            self._load_without_lock()

    def _save(self) -> None:
        """Save cache data to JSON file with file locking."""
        try:
            # Ensure directory exists
            cache_dir = os.path.dirname(self.cache_file)
            if cache_dir and not os.path.exists(cache_dir):
                os.makedirs(cache_dir, exist_ok=True, mode=0o755)

            # Use file locking to prevent race conditions
            with open(self.cache_file, "w", encoding="utf-8") as f:
                try:
                    lock_file(f, exclusive=True)
                    json.dump(self._cache, f, indent=2, ensure_ascii=False)
                    f.flush()  # Ensure data is written to disk
                    os.fsync(f.fileno())  # Force write to disk
                finally:
                    unlock_file(f)

            # Set file permissions to be readable/writable by owner and group (Unix only)
            if sys.platform != "win32":
                os.chmod(self.cache_file, 0o664)

        except PermissionError as e:
            logger.error(
                f"Permission denied writing cache file '{self.cache_file}': {e}. "
                f"Check directory/file permissions and ownership."
            )
        except IOError as e:
            logger.error(f"Error saving cache file: {e}")

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set a value in the cache with optional TTL.
        Reloads cache from disk before setting to ensure consistency in multi-threaded environments.

        Args:
            key (str): Cache key
            value (Any): Value to store (must be JSON serializable)
            ttl (int, optional): Time-to-live in seconds (uses default_ttl if not provided)

        Returns:
            bool: True if successful, False otherwise
        """
        # Check for falsy values if allow_falsy is False
        # Note: We explicitly check for each falsy value type to ensure proper handling
        if not self.allow_falsy:
            # Check if value is falsy (None, False, 0, 0.0, "", [], {}, etc.)
            if (
                value is None
                or value is False
                or (
                    isinstance(value, (str, list, dict, tuple, set)) and len(value) == 0
                )
                or (isinstance(value, (int, float)) and value == 0)
            ):
                logger.warning(
                    f"Attempted to cache falsy value for key '{key}': {value!r}. "
                    f"Ignoring. Set allow_falsy=True to cache falsy values."
                )
                return False

        if ttl is None:
            ttl = self.default_ttl

        expires_at = time.time() + ttl

        with self._lock:
            try:
                # Reload from disk to get latest data (important for multi-instance scenarios)
                self._load_without_lock()

                self._cache[key] = {
                    "value": value,
                    "expires_at": expires_at,
                    "created_at": time.time(),
                }
                self._save()

                logger.debug(f"Cache set for key: {key}")
                return True
            except (TypeError, ValueError) as e:
                logger.error(f"Error setting cache key '{key}': {e}")
                return False

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value from the cache.
        Reloads from disk to ensure we have the latest data in multi-instance scenarios.

        Args:
            key (str): Cache key
            default (Any): Default value to return if key not found or expired

        Returns:
            Any: Cached value or default
        """
        with self._lock:
            # Reload from disk to get latest data
            self._load_without_lock()

            if key not in self._cache:
                return default

            entry = self._cache[key]

            # Check if expired
            if time.time() > entry["expires_at"]:
                del self._cache[key]
                self._save()
                return default

            logger.debug(f"Cache hit for key: {key}")
            return entry["value"]

    def has(self, key: str) -> bool:
        """
        Check if a key exists in the cache and is not expired.

        Args:
            key (str): Cache key

        Returns:
            bool: True if key exists and is valid, False otherwise
        """
        with self._lock:
            if key not in self._cache:
                return False

            # Check if expired
            if time.time() > self._cache[key]["expires_at"]:
                del self._cache[key]
                self._save()
                return False

            return True

    def delete(self, key: str) -> bool:
        """
        Delete a key from the cache.

        Args:
            key (str): Cache key to delete

        Returns:
            bool: True if key was deleted, False if key didn't exist
        """
        with self._lock:
            # Reload from disk to get latest data
            self._load_without_lock()

            if key in self._cache:
                del self._cache[key]
                self._save()
                return True
            return False

    def clear(self) -> int:
        """
        Clear all entries from the cache.

        Returns:
            int: Number of entries cleared
        """
        with self._lock:
            count = len(self._cache)
            self._cache = {}
            self._save()
            return count

    def cleanup(self) -> int:
        """
        Remove all expired entries from the cache.

        Returns:
            int: Number of entries removed
        """
        with self._lock:
            current_time = time.time()
            expired_keys = [
                key
                for key, entry in self._cache.items()
                if current_time > entry["expires_at"]
            ]

            for key in expired_keys:
                del self._cache[key]

            if expired_keys:
                self._save()

            return len(expired_keys)

    def stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            dict: Dictionary containing cache statistics including:
                - total_entries: Total number of cached entries
                - expired_entries: Number of expired entries
                - valid_entries: Number of valid (non-expired) entries
                - cache_file: Path to cache file
                - cache_size_bytes: Size of cache file in bytes
                - oldest_entry: Timestamp of oldest entry
                - newest_entry: Timestamp of newest entry
        """
        with self._lock:
            current_time = time.time()

            valid_entries = []
            expired_entries = []

            for key, entry in self._cache.items():
                if current_time > entry["expires_at"]:
                    expired_entries.append(key)
                else:
                    valid_entries.append(entry)

            cache_size = 0
            if os.path.exists(self.cache_file):
                cache_size = os.path.getsize(self.cache_file)

            oldest_entry = None
            newest_entry = None

            if valid_entries:
                created_times = [entry["created_at"] for entry in valid_entries]
                oldest_entry = datetime.fromtimestamp(min(created_times)).isoformat()
                newest_entry = datetime.fromtimestamp(max(created_times)).isoformat()

            return {
                "total_entries": len(self._cache),
                "expired_entries": len(expired_entries),
                "valid_entries": len(valid_entries),
                "cache_file": self.cache_file,
                "cache_size_bytes": cache_size,
                "cache_size_kb": round(cache_size / 1024, 2),
                "oldest_entry": oldest_entry,
                "newest_entry": newest_entry,
                "default_ttl_hours": self.default_ttl / 3600,
            }

    def get_all_keys(self) -> list:
        """
        Get all valid (non-expired) keys in the cache.

        Returns:
            list: List of valid cache keys
        """
        with self._lock:
            current_time = time.time()
            return [
                key
                for key, entry in self._cache.items()
                if current_time <= entry["expires_at"]
            ]

    def get_ttl(self, key: str) -> Optional[int]:
        """
        Get the remaining time-to-live for a key in seconds.

        Args:
            key (str): Cache key

        Returns:
            int: Remaining TTL in seconds, or None if key doesn't exist
        """
        with self._lock:
            if key not in self._cache:
                return None

            entry = self._cache[key]
            remaining = entry["expires_at"] - time.time()

            if remaining <= 0:
                del self._cache[key]
                self._save()
                return None

            return int(remaining)

    def extend_ttl(self, key: str, additional_seconds: int) -> bool:
        """
        Extend the TTL of an existing cache entry.

        Args:
            key (str): Cache key
            additional_seconds (int): Additional seconds to add to TTL

        Returns:
            bool: True if successful, False if key doesn't exist
        """
        with self._lock:
            # Reload from disk to get latest data
            self._load_without_lock()

            if key not in self._cache:
                return False

            # Check if already expired
            if time.time() > self._cache[key]["expires_at"]:
                del self._cache[key]
                self._save()
                return False

            self._cache[key]["expires_at"] += additional_seconds
            self._save()
            return True

    def refresh(self) -> None:
        """
        Reload cache data from the JSON file.
        Useful when multiple processes might be modifying the cache.
        """
        self._load()
        if self.auto_cleanup:
            self.cleanup()

    def __contains__(self, key: str) -> bool:
        """Support for 'in' operator."""
        return self.has(key)

    def __len__(self) -> int:
        """Return the number of valid cache entries."""
        return len(self.get_all_keys())

    def __repr__(self) -> str:
        """String representation of the cache."""
        stats = self.stats()
        return f"Cache(file='{self.cache_file}', entries={stats['valid_entries']}, size={stats['cache_size_kb']}KB)"


# Example usage
if __name__ == "__main__":
    # Initialize cache with default 24-hour TTL
    cache = Cache(cache_file="example_cache.json")

    # Set values
    cache.set("user_123", {"name": "John Doe", "email": "john@example.com"})
    cache.set("api_token", "secret_token_xyz", ttl=3600)  # 1 hour TTL
    cache.set("temp_data", "temporary", ttl=60)  # 1 minute TTL

    # Attempting to set falsy values (will be ignored by default)
    cache.set("empty_string", "")  # Will be rejected with warning
    cache.set("none_value", None)  # Will be rejected with warning
    cache.set("empty_list", [])  # Will be rejected with warning

    # To allow falsy values, create cache with allow_falsy=True
    cache_with_falsy = Cache(cache_file="example_cache_falsy.json", allow_falsy=True)
    cache_with_falsy.set("empty_string", "")  # Will be accepted
    cache_with_falsy.set("false_value", False)  # Will be accepted
    cache_with_falsy.set("zero_value", 0)  # Will be accepted

    # Get values
    user = cache.get("user_123")
    print(f"User data: {user}")

    # Check if key exists
    if "api_token" in cache:
        print("API token exists in cache")

    # Get TTL
    ttl = cache.get_ttl("api_token")
    print(f"API token expires in {ttl} seconds")

    # Get all keys
    keys = cache.get_all_keys()
    print(f"All cache keys: {keys}")

    # Get statistics
    stats = cache.stats()
    print(f"\nCache Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # Cleanup expired entries
    removed = cache.cleanup()
    print(f"\nRemoved {removed} expired entries")

    # Clear all cache
    # cleared = cache.clear()
    # print(f"Cleared {cleared} entries")
