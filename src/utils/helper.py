from datetime import datetime
import random
import time
from log.logging import logger
import os


# Helper method to generate date strings for YouTube API
def get_date_string(date: datetime) -> str:
    """Convert datetime to YouTube API format (ISO 8601)"""
    return date.strftime("%Y-%m-%dT%H:%M:%SZ")


def get_today_start() -> str:
    """Get today's date at 00:00:00 UTC in YouTube API format"""
    today = datetime.utcnow().replace(hour=0, minute=0, second=0)
    return get_date_string(today)


def get_today_end() -> str:
    """Get today's date at 23:59:59 UTC in YouTube API format"""
    today = datetime.utcnow().replace(hour=23, minute=59, second=59)
    return get_date_string(today)


def request_delay(attempt: int = 1):
    retry_delay_base = 1  # Base delay in seconds
    delay = retry_delay_base * (2**attempt) + random.uniform(1, 10)
    logger.info(f"Retrying in {delay:.2f} seconds...")
    time.sleep(delay)


def _load_proxies_from_file():
    proxies = []
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(base_dir, "proxies.txt")
        if not os.path.exists(file_path):
            return proxies
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split(":")
                if len(parts) != 4:
                    continue
                host, port, username, password = parts
                cred = f"{username}:{password}@{host}:{port}"
                url = f"http://{cred}/"
                proxies.append({"http": url, "https": url})
    except Exception:
        # If anything fails, return what we have
        pass
    return proxies
