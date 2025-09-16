import time
import requests
import random
from typing import Any, Dict, Union
from config.transcript_config import (
    RATE_LIMIT_DELAY,
    MAX_RETRIES,
    BACKOFF_MULTIPLIER,
    MAX_PROXY_ATTEMPTS,
    EXTENDED_DELAY,
    PROXY_VALIDATION_TIMEOUT,
    get_effective_proxy_list,
    is_ip_blocking_error,
)
from youtube_transcript_api.proxies import GenericProxyConfig
from log.logging import logger
from utils.text_clean import clean_text
from classes.Response import Response
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api import TranscriptsDisabled, NoTranscriptFound


class Transcript:

    def __init__(self, video_id: str):
        self.video_id = video_id

    def _validate_proxy(self, proxy_url: str) -> bool:
        """Test if a proxy is working"""
        try:
            proxies = {"http": proxy_url, "https": proxy_url}
            response = requests.get(
                "http://httpbin.org/ip",
                proxies=proxies,
                timeout=PROXY_VALIDATION_TIMEOUT,
            )
            return response.status_code == 200
        except:
            return False

    def _get_working_proxy(self) -> Union[GenericProxyConfig, None]:
        """Get a working proxy from the list"""
        # Shuffle the list to try different proxies each time
        shuffled_proxies = get_effective_proxy_list().copy()
        random.shuffle(shuffled_proxies)

        for proxy_url in shuffled_proxies:
            logger.debug(f"Testing proxy: {proxy_url}")
            if self._validate_proxy(proxy_url):
                logger.info(f"Found working proxy: {proxy_url}")
                return GenericProxyConfig(http_url=proxy_url, https_url=proxy_url)

        logger.warning("No working proxies found")
        return None

    def _exponential_backoff(self, attempt: int) -> None:
        """
        Exponential backoff is a strategy that increases the wait time between retries
        after a failure, typically by multiplying the delay by a constant factor each time.
        It is used to reduce the load on a resource (such as an API or network service)
        and to avoid overwhelming the server or triggering rate limits when repeated requests fail.

        This method applies exponential backoff by increasing the delay after each failed attempt.
        """
        delay = RATE_LIMIT_DELAY * (BACKOFF_MULTIPLIER**attempt)
        max_delay = 60  # Maximum 1 minute delay
        delay = min(delay, max_delay)
        logger.info(
            f"Applying backoff delay: {delay:.2f} seconds (attempt {attempt + 1})"
        )
        time.sleep(delay)

    def _process_transcript_data(self, raw_data):
        """Process raw transcript data to ensure proper text encoding"""
        processed_data = []
        for snippet in raw_data:
            start = snippet.get("start", 0)
            duration = snippet.get("duration", 0)
            text = clean_text(snippet.get("text", ""))

            processed_snippet = {
                "text": text,
                "start": start,
                "duration": duration,
            }
            processed_data.append(processed_snippet)
        return processed_data

    def _fetch_transcript(self, use_proxy=False, proxy_config=None) -> Response:
        """Get transcript with exponential backoff and retry logic"""

        for attempt in range(MAX_RETRIES):
            try:
                if attempt > 0:
                    self._exponential_backoff(attempt)

                if use_proxy and proxy_config:
                    ytt_api = YouTubeTranscriptApi(proxy_config=proxy_config)
                    logger.info(f"Using proxy for video {self.video_id}")
                else:
                    ytt_api = YouTubeTranscriptApi()
                    logger.info(f"Direct connection for video {self.video_id}")

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

            except Exception as e:
                error_message = str(e)

                # Check if it's an IP blocking error
                if is_ip_blocking_error(error_message):
                    logger.warning(
                        f"IP blocking detected for video {self.video_id}, attempt {attempt + 1}"
                    )
                    if attempt < MAX_RETRIES - 1:
                        continue  # Retry with backoff
                else:
                    logger.error(
                        f"Non-blocking error for video {self.video_id}: {error_message}"
                    )

                # On final attempt or non-blocking error, return error
                if attempt == MAX_RETRIES - 1:
                    return Response.error(
                        status_code=500,
                        message=f"Failed to retrieve transcript after {MAX_RETRIES} attempts for video {self.video_id}: {error_message}",
                    )

        return Response.error(
            status_code=500,
            message=f"All retry attempts failed for video {self.video_id}",
        )

    def _fetch_transcript_with_proxies(self) -> Response:
        """Get transcript using proxies - advanced fallback method"""

        # Strategy 1: Try a pre-validated working proxy
        working_proxy = self._get_working_proxy()

        if working_proxy:
            response = self._fetch_transcript(
                use_proxy=True, proxy_config=working_proxy
            )
            if response.status_code == 200:
                return response

        # Strategy 2: Try multiple proxies with retry logic
        logger.info(f"Trying multiple proxies for video {self.video_id}")

        shuffled_proxies = get_effective_proxy_list().copy()
        random.shuffle(shuffled_proxies)

        # Try up to 5 different proxies
        max_proxy_attempts = min(MAX_PROXY_ATTEMPTS, len(shuffled_proxies))

        for attempt, proxy_url in enumerate(shuffled_proxies[:max_proxy_attempts]):
            try:
                logger.info(
                    f"Attempting proxy {proxy_url} for video {self.video_id} (attempt {attempt + 1}/{max_proxy_attempts})"
                )

                proxy_config = GenericProxyConfig(
                    http_url=proxy_url, https_url=proxy_url
                )

                # Use the retry logic for this proxy
                response = self._fetch_transcript(
                    use_proxy=True, proxy_config=proxy_config
                )

                if response.status_code == 200:
                    logger.success(
                        f"Successfully retrieved transcript via proxy {proxy_url} for video {self.video_id}"
                    )
                    return response

                elif response.status_code in [403, 404]:
                    return response

                else:
                    logger.warning(
                        f"Proxy {proxy_url} failed for video {self.video_id}: {response.message}"
                    )
                    continue

            except Exception as e:
                logger.warning(
                    f"Proxy {proxy_url} failed unexpectedly for video {self.video_id}: {str(e)}"
                )
                continue

        return Response.error(
            status_code=500,
            message=f"All {max_proxy_attempts} proxy attempts failed for video {self.video_id}",
        )

    def fetch(self) -> Union[Dict[str, Any], None]:
        """
        Get transcript for a video using multiple advanced strategies to avoid IP blocking

        Strategies:
        1. Direct connection with exponential backoff
        2. Pre-validated proxy with retry logic
        3. Multiple proxy attempts with retry logic
        4. Extended delay and final retry
        """

        response = self._fetch_transcript()

        if response.status_code == 200:
            return response.data

        # Check for definitive errors (no point in retrying)
        if response.status_code in [403, 404]:
            return None

        # Strategy 2: Advanced proxy-based retrieval
        logger.warning(
            f"Strategy 2: Using proxy-based retrieval for video {self.video_id}"
        )

        response = self._fetch_transcript_with_proxies()

        if response.status_code == 200:
            logger.success(f"Proxy connection successful for video {self.video_id}")
            return response.data

        # Check for definitive errors again
        if response.status_code in [403, 404]:
            logger.error(
                f"Definitive error via proxy for video {self.video_id}: {response.message}"
            )
            return None

        # Strategy 3: Extended delay and final retry
        logger.warning(
            f"Strategy 3: Extended delay and final retry for video {self.video_id}"
        )
        logger.info(f"All proxy attempts failed, applying extended delay...")

        # Apply a longer delay to let IP restrictions potentially reset
        time.sleep(EXTENDED_DELAY)

        # Final attempt with direct connection
        logger.info(f"Final attempt with direct connection for video {self.video_id}")
        final_response = self._fetch_transcript()

        if final_response.status_code == 200:
            logger.success(f"Final attempt successful for video {self.video_id}")
            return final_response.data

        return None  # No transcript available after all strategies
