import os
import time
import random
from typing import Any, Dict, Union, Optional, List
from youtube_transcript_api.proxies import GenericProxyConfig
from log.logging import logger
from utils.helper import request_delay
from utils.text_clean import clean_text
from classes.Response import Response
from youtube_transcript_api import (
    YouTubeTranscriptApi,
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
    CouldNotRetrieveTranscript,
    IpBlocked,
    RequestBlocked,
)
from youtube_transcript_api.proxies import WebshareProxyConfig
import requests
from requests.exceptions import ProxyError, ConnectTimeout, ReadTimeout, ConnectionError
from classes.IPManager import IPManager
from dotenv import load_dotenv

load_dotenv()


class Transcript:
    def __init__(self, video_id: str):
        self.video_id = video_id
        self.domain = "youtube.com"

        # Initialize cooldown manager
        self.cooldown_manager = IPManager(cooldown_minutes=180)

        # Get credentials from environment variables (more secure)
        self.username = os.getenv("WEBSHARE_USERNAME", "ronwokiy")
        self.password = os.getenv("WEBSHARE_PASSWORD", "3g2fhwga4d21")
        self.proxy_host = os.getenv("WEBSHARE_HOST", "proxy.webshare.io")
        self.proxy_port = os.getenv("WEBSHARE_PORT", "80")

        # Multiple proxy endpoints for failover
        self.proxy_ports = ["80", "1080", "8080"]
        self.proxy_urls = [
            f"http://{self.username}:{self.password}@{self.proxy_host}:{port}"
            for port in self.proxy_ports
        ]

        # Configuration
        self.max_retries = 5
        self.timeout = 30  # Request timeout in seconds

        # Error patterns that indicate blocking/rate limiting
        self.blocking_indicators = [
            "403",
            "blocked",
            "rate limit",
            "too many requests",
            "forbidden",
            "access denied",
        ]

    def _process_transcript_data(self, raw_data: List[Dict]) -> List[Dict]:
        """Process raw transcript data to ensure proper text encoding and validation"""
        processed_data = []

        for snippet in raw_data:
            try:
                start = float(snippet.get("start", 0))
                duration = float(snippet.get("duration", 0))
                text = clean_text(snippet.get("text", ""))

                # Skip empty or invalid snippets
                if not text.strip():
                    continue

                processed_snippet = {
                    "text": text,
                    "start": start,
                    "duration": duration,
                }
                processed_data.append(processed_snippet)

            except (ValueError, TypeError) as e:
                logger.warning(
                    f"Skipping invalid transcript snippet: {snippet}, Error: {e}"
                )
                continue

        return processed_data

    def _is_blocking_error(self, error_message: str, status_code: int = None) -> bool:
        """Check if error indicates IP blocking/rate limiting"""
        error_lower = error_message.lower()

        # Check status codes that indicate blocking
        if status_code in [403, 429, 503]:
            return True

        # Check error message patterns
        for indicator in self.blocking_indicators:
            if indicator in error_lower:
                return True

        return False

    def _fetch_transcript(self, use_proxy=False, proxy_config=None) -> Response:
        """Get transcript - simplified since WebShare handles retries and proxy rotation"""

        try:
            if use_proxy and proxy_config:
                ytt_api = YouTubeTranscriptApi(proxy_config=proxy_config)
            else:
                ytt_api = YouTubeTranscriptApi()

            transcripts = {}
            transcript_list = ytt_api.list(self.video_id)

            for transcript in transcript_list:
                transcript_data = transcript.fetch()
                raw_data = transcript_data.to_raw_data()

                # Process the raw data to ensure proper text handling
                processed_data = self._process_transcript_data(raw_data)

                transcripts[transcript.language_code] = {
                    "language": transcript.language_code,
                    "language_name": transcript.language,
                    "is_generated": transcript.is_generated,
                    "is_translatable": transcript.is_translatable,
                    "data": processed_data,
                }

            if transcripts:
                return Response.success(
                    status_code=200,
                    message=f"Successfully retrieved transcript for video {self.video_id}"
                    + (" (via proxy)" if use_proxy else " (direct)"),
                    data=transcripts,
                )

        except TranscriptsDisabled:
            return Response.forbidden(
                message=f"Transcripts are disabled for this video {self.video_id}",
            )

        except NoTranscriptFound:
            return Response.not_found(
                message=f"No transcript found for this video {self.video_id}",
            )

        except (IpBlocked, RequestBlocked):
            return Response.too_many_requests(
                message=f"IP is blocked for video {self.video_id}",
            )

        except (
            ProxyError,
            ConnectTimeout,
            ReadTimeout,
            ConnectionError,
            TimeoutError,
        ) as e:
            return Response.error(
                status_code=500,
                message=f"Network error when fetching transcript for video {self.video_id}: {str(e)}",
            )

        except CouldNotRetrieveTranscript as e:
            return Response.error(
                status_code=500,
                message=f"Could not retrieve transcript for video {self.video_id}: {str(e)}",
            )

        except Exception as e:
            return Response.error(
                status_code=500,
                message=f"Failed to retrieve transcript for video {self.video_id}: {str(e)}",
            )

    def get_transcript_text(self, language_code: Optional[str] = None) -> Optional[str]:
        """
        Get transcript as plain text string

        Args:
            language_code: Specific language code to get. If None, gets first available.

        Returns:
            Plain text transcript or None if not available
        """
        transcripts = self.fetch()
        if not transcripts:
            return None

        # If specific language requested
        if language_code and language_code in transcripts:
            transcript_data = transcripts[language_code]["data"]
        else:
            # Get first available transcript
            first_lang = next(iter(transcripts))
            transcript_data = transcripts[first_lang]["data"]

        # Join all text segments
        return " ".join([segment["text"] for segment in transcript_data])

    def fetch(self) -> Union[Dict[str, Any], None]:
        """
        Get transcript for a video with IP cooldown tracking and comprehensive error handling

        Strategies:
        1. Check if IP is in cooldown, skip direct connection if so
        2. Try direct connection first (if not in cooldown)
        3. Try WebShare proxy if direct fails or is in cooldown
        """

        request_delay()
        ip_in_cooldown = self.cooldown_manager.is_ip_in_cooldown()
        if ip_in_cooldown:
            remaining = self.cooldown_manager.get_cooldown_remaining()
            logger.warning(f"System IP is in cooldown for {remaining} more minutes")

        if not ip_in_cooldown:
            response = self._fetch_transcript()

            if response.status_code == 200:
                return response.data

            if response.status_code in [403, 404, 503]:
                return None

            if response.status_code in [429]:
                self.cooldown_manager.add_ip_to_cooldown()

        proxy_config = WebshareProxyConfig(
            proxy_username=self.username,
            proxy_password=self.password,
            retries_when_blocked=self.max_retries,
        )

        response = self._fetch_transcript(
            use_proxy=True,
            proxy_config=proxy_config,
        )

        if response.status_code == 200:
            return response.data

        logger.error(
            f"All strategies failed for video {self.video_id}: {response.message}"
        )
        return None
