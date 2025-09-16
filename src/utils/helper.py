from datetime import datetime
import random
import time


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


def rate_limit_delay():
    delay = random.uniform(2, 6)
    time.sleep(delay)
