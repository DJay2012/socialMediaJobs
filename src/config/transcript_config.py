"""
Configuration for YouTube Transcript Anti-Blocking System
"""

import os
from typing import List, Dict, Any

# Variable configurations
RATE_LIMIT_DELAY = 10
MAX_RETRIES = 2
BACKOFF_MULTIPLIER = 2
EXTENDED_DELAY = 30
MAX_PROXY_ATTEMPTS = 3

# Enable/disable proxy validation (can be slow)
VALIDATE_PROXIES = True
PROXY_VALIDATION_TIMEOUT = 10

# Strategy configuration
ENABLE_EXTENDED_DELAY_STRATEGY = True
ENABLE_PROXY_STRATEGIES = True

# Premium proxy configurations (if available)
PREMIUM_PROXIES: List[Dict[str, Any]] = []

# Advanced free proxy list with geographic diversity
# Updated regularly to maintain effectiveness
FREE_PROXY_LIST = [
    # Tier 1: Residential-like proxies (highest success rate)
    "http://198.49.68.80:80",  # US - Residential-like
    "http://143.198.228.250:80",  # US - DigitalOcean
    "http://165.227.81.188:9999",  # US - VPS
    "http://138.68.161.14:32231",  # US - Cloud
    "http://167.172.173.210:37825",  # US - Different provider
    # Tier 2: International proxies (geographic diversity)
    "http://103.152.112.162:80",  # IN - India
    "http://154.236.168.181:1981",  # ZA - South Africa
    "http://185.199.229.156:7492",  # DE - Germany
    "http://103.149.162.194:80",  # TH - Thailand
    "http://41.33.219.141:8080",  # EG - Egypt
    "http://200.116.226.210:43049",  # BR - Brazil
    "http://103.81.85.129:22884",  # PK - Pakistan
    "http://45.190.79.164:999",  # CO - Colombia
    # Tier 3: SOCKS5 proxies (better for avoiding detection)
    "socks5://198.23.239.134:13780",  # US
    "socks5://72.210.252.134:46164",  # US
    "socks5://184.178.172.28:15294",  # US
    # Tier 4: HTTPS proxies (encrypted)
    "https://198.49.68.80:443",
    "https://143.198.228.250:443",
    "https://185.199.229.156:443",
    # Tier 5: Rotating proxy services (if you have access)
    # "http://rotating.proxy.service.com:8080",
    "http://104.18.41.150:2087",
]

# Proxy effectiveness tracking (updated based on success rates)
# Add failed proxies here to avoid them in future attempts
PROXY_BLACKLIST = []

# User agent rotation for additional obfuscation
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
]

# Error patterns for IP blocking detection
IP_BLOCKING_PATTERNS = [
    "blocked",
    "ip",
    "requests from your ip",
    "cloud provider",
    "too many requests",
    "rate limit",
    "403",
    "forbidden",
]


def get_effective_proxy_list() -> List[str]:
    """Get the effective proxy list (excluding blacklisted ones)"""
    return [proxy for proxy in FREE_PROXY_LIST if proxy not in PROXY_BLACKLIST]


def is_ip_blocking_error(error_message: str) -> bool:
    """Check if an error message indicates IP blocking"""
    error_lower = error_message.lower()
    return any(pattern in error_lower for pattern in IP_BLOCKING_PATTERNS)


def add_to_blacklist(proxy_url: str):
    """Add a proxy to the blacklist"""
    if proxy_url not in PROXY_BLACKLIST:
        PROXY_BLACKLIST.append(proxy_url)


def get_config_summary() -> Dict[str, Any]:
    """Get a summary of current configuration"""
    return {
        "rate_limit_delay": RATE_LIMIT_DELAY,
        "max_retries": MAX_RETRIES,
        "backoff_multiplier": BACKOFF_MULTIPLIER,
        "extended_delay": EXTENDED_DELAY,
        "max_proxy_attempts": MAX_PROXY_ATTEMPTS,
        "validate_proxies": VALIDATE_PROXIES,
        "proxy_timeout": PROXY_VALIDATION_TIMEOUT,
        "enable_extended_delay": ENABLE_EXTENDED_DELAY_STRATEGY,
        "enable_proxies": ENABLE_PROXY_STRATEGIES,
        "total_free_proxies": len(FREE_PROXY_LIST),
        "effective_proxies": len(get_effective_proxy_list()),
        "blacklisted_proxies": len(PROXY_BLACKLIST),
        # "premium_proxies": len(PREMIUM_PROXIES),
    }
