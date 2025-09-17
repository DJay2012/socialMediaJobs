import os
import json
from typing import Any, Dict, Optional
from datetime import datetime, timedelta
from log.logging import logger
import requests


class IPManager:
    """Manages IP-based cooldown periods to prevent repeated attempts when blocked"""

    def __init__(self, cooldown_file="temp/ip_cooldown.json", cooldown_minutes=30):
        self.cooldown_file = cooldown_file
        self.cooldown_duration = timedelta(minutes=cooldown_minutes)
        self.system_ip = None
        self._load_cooldown_data()

    def _load_cooldown_data(self):
        """Load existing cooldown data from file"""
        try:
            if os.path.exists(self.cooldown_file):
                with open(self.cooldown_file, "r") as f:
                    self.cooldown_data = json.load(f)
            else:
                self.cooldown_data = {}
        except Exception as e:
            logger.warning(f"Could not load cooldown data: {e}")
            self.cooldown_data = {}

    def _save_cooldown_data(self):
        """Save cooldown data to file"""
        try:
            with open(self.cooldown_file, "w") as f:
                json.dump(self.cooldown_data, f, default=str)
        except Exception as e:
            logger.warning(f"Could not save cooldown data: {e}")

    def _get_system_ip(self) -> Optional[str]:
        """Get the current system's public IP address"""
        if self.system_ip:
            return self.system_ip

        try:
            # Try multiple IP detection services
            services = [
                "https://api.ipify.org",
                "https://httpbin.org/ip",
                "https://api.myip.com",
                "https://ipinfo.io/ip",
            ]

            for service in services:
                try:
                    if service == "https://httpbin.org/ip":
                        response = requests.get(service, timeout=5)
                        self.system_ip = (
                            response.json().get("origin", "").split(",")[0].strip()
                        )
                    else:
                        response = requests.get(service, timeout=5)
                        self.system_ip = response.text.strip()

                    if self.system_ip and len(self.system_ip.split(".")) == 4:
                        logger.info(f"Detected system IP: {self.system_ip}")
                        return self.system_ip
                except Exception:
                    continue

        except Exception as e:
            logger.warning(f"Could not detect system IP: {e}")

        return None

    def is_ip_in_cooldown(self) -> bool:
        """Check if the current IP is in cooldown period"""
        ip = self._get_system_ip()
        if not ip:
            return False

        if ip in self.cooldown_data:
            cooldown_time = datetime.fromisoformat(self.cooldown_data[ip])
            if datetime.now() < cooldown_time:
                remaining = cooldown_time - datetime.now()
                logger.warning(
                    f"IP {ip} is in cooldown for {remaining.seconds // 60} more minutes"
                )
                return True
            else:
                # Cooldown expired, remove it
                del self.cooldown_data[ip]
                self._save_cooldown_data()

        return False

    def add_ip_to_cooldown(self):
        """Add current IP to cooldown period"""
        ip = self._get_system_ip()
        if not ip:
            return

        cooldown_until = datetime.now() + self.cooldown_duration
        self.cooldown_data[ip] = cooldown_until.isoformat()
        self._save_cooldown_data()

        logger.warning(
            f"IP {ip} added to cooldown until {cooldown_until.strftime('%Y-%m-%d %H:%M:%S')}"
        )

    def get_cooldown_remaining(self) -> Optional[int]:
        """Get remaining cooldown time in minutes"""
        ip = self._get_system_ip()
        if not ip or ip not in self.cooldown_data:
            return None

        cooldown_time = datetime.fromisoformat(self.cooldown_data[ip])
        if datetime.now() < cooldown_time:
            remaining = cooldown_time - datetime.now()
            return remaining.seconds // 60

        return None

    def get_cooldown_status(self) -> Dict[str, Any]:
        """Get current cooldown status information"""
        remaining = self.get_cooldown_remaining()
        system_ip = self._get_system_ip()

        return {
            "system_ip": system_ip,
            "in_cooldown": remaining is not None,
            "remaining_minutes": remaining,
            "will_skip_direct": remaining is not None,
        }

    def clear_cooldown(self) -> bool:
        """Manually clear cooldown for current IP (use with caution)"""
        try:
            ip = self._get_system_ip()
            if ip and ip in self.cooldown_data:
                del self.cooldown_data[ip]
                self._save_cooldown_data()
                logger.info(f"Cleared cooldown for IP {ip}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to clear cooldown: {e}")
            return False
