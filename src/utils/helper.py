from datetime import datetime, date
import random
import time
from log.logging import logger
import os
from dateutil import parser
import isodate


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


def request_delay():
    delay = random.uniform(2, 5)
    logger.info(f"Waiting for {delay:.2f} seconds...")
    time.sleep(delay)


def normalize_to_datetime(date_str):
    try:
        if date_str is None:
            return None

        return parser.parse(date_str)
    except (ValueError, TypeError) as e:
        raise ValueError(f"Could not parse date string: {date_str}") from e


def format_date(date_input, format_string="%Y-%m-%d %H:%M:%S"):
    """
    Universal date formatting utility that handles both string and datetime objects.

    Args:
        date_input: Can be a string, datetime, or date object
        format_string (str): The format string to use with strftime (default: "%Y-%m-%d %H:%M:%S")

    Returns:
        str: Formatted date string

    Raises:
        ValueError: If the input cannot be converted to a datetime object

    Examples:
        format_date("2023-12-25")  # Returns: "2023-12-25 00:00:00"
        format_date(datetime.now(), "%Y-%m-%d")  # Returns: "2023-12-25"
        format_date(date(2023, 12, 25), "%B %d, %Y")  # Returns: "December 25, 2023"
    """
    try:
        # If it's already a datetime object, use it directly
        if isinstance(date_input, datetime):
            return date_input.strftime(format_string)

        # If it's a date object, convert to datetime
        elif isinstance(date_input, date):
            # Convert date to datetime at midnight
            dt = datetime.combine(date_input, datetime.min.time())
            return dt.strftime(format_string)

        # If it's a string, parse it first
        elif isinstance(date_input, str):
            # Try to parse the string using dateutil parser
            parsed_date = parser.parse(date_input)
            return parsed_date.strftime(format_string)

        # If it's None, return empty string or current datetime
        elif date_input is None:
            return datetime.now().strftime(format_string)

        else:
            raise ValueError(f"Unsupported date type: {type(date_input)}")

    except Exception as e:
        print(f"Error formatting date '{date_input}': {str(e)}")
        raise ValueError(f"Could not format date '{date_input}': {str(e)}") from e


def format_youtube_duration(duration: str) -> str:
    """
    Convert YouTube API ISO 8601 duration string into a human-readable format.
    Days are converted into hours.

    Examples:
        PT1H2M30S -> "1:02:30"
        PT2M5S    -> "2:05"
        PT45S     -> "0:45"
        P4DT4H1S  -> "100:00:01"  (4 days = 96 hours + 4 = 100)
    """
    if not duration:
        return ""

    # Parse ISO 8601 duration into timedelta
    td = isodate.parse_duration(duration)
    total_seconds = int(td.total_seconds())

    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    return (
        f"{hours}:{minutes:02d}:{seconds:02d}"
        if hours > 0
        else f"{minutes}:{seconds:02d}"
    )


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
