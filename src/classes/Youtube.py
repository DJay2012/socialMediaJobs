from types import FunctionType
from config.CredentialManager import credential_manager
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from log.logging import logger
from classes.YoutubeCaptions import YoutubeCaptions


class Youtube:

    def __init__(self):
        self.logger = logger
        self.api_key = None
        self.captions_api = None

        credential_manager.reactivate_keys()
        api_key = credential_manager.get_api_key(
            "youtube", test_func=self._test_api_key
        )

        if not api_key:
            raise Exception("No available YouTube API keys")

        self.api_key = api_key
        self._build = self._initialize_build()

        # Initialize captions API
        try:
            self.captions_api = YoutubeCaptions()
            self.logger.success("YouTube Captions API initialized")
        except Exception as e:
            self.logger.warning(f"Failed to initialize YouTube Captions API: {e}")

    def _handle_api_error(self, error: HttpError):

        # Handle API errors and report them to the API key manager
        if error.resp.status == 403:
            # Check for quota exceeded
            if "quotaExceeded" in str(error) or "quota" in str(error).lower():
                self.logger.warning(
                    "YouTube API quota exceeded, reporting error to key manager"
                )

                credential_manager.report_error(
                    "youtube", self.api_key, "quota_exceeded"
                )
                return True

            # Check for blocked/forbidden requests
            elif "blocked" in str(error).lower() or "forbidden" in str(error).lower():
                self.logger.warning(
                    f"YouTube API request blocked for key, reporting error to key manager: {str(error)}"
                )

                credential_manager.report_error("youtube", self.api_key, "invalid_key")
                return True

            # Generic 403 error
            else:
                self.logger.warning(
                    f"YouTube API 403 error, reporting error to key manager: {str(error)}"
                )

                credential_manager.report_error("youtube", self.api_key, "invalid_key")
                return True

        elif error.resp.status == 401:
            self.logger.error(
                "YouTube API authentication failed, reporting invalid key"
            )

            credential_manager.report_error("youtube", self.api_key, "invalid_key")
            return True

        elif error.resp.status == 429:
            self.logger.warning(
                "YouTube API rate limit exceeded, reporting error to key manager"
            )

            credential_manager.report_error("youtube", self.api_key, "rate_limit")
            return True

        return False  # Don't retry for other errors

    def _test_api_key(self, api_key: str) -> bool:

        try:
            test_service = build("youtube", "v3", developerKey=api_key)
            # Make a simple request to test the key
            request = test_service.search().list(
                q="test", part="snippet", type="video", maxResults=1
            )
            request.execute()
            return True
        except HttpError as e:
            if e.resp.status == 403:
                self.logger.error(f"API key test failed with 403: {str(e)}")
                return False
            elif e.resp.status == 401:
                self.logger.error(f"API key test failed with 401: {str(e)}")
                return False
            else:
                self.logger.error(
                    f"API key test failed with status {e.resp.status}: {str(e)}"
                )
                return False
        except Exception as e:
            self.logger.error(f"API key test failed with unexpected error: {str(e)}")
            return False

    def _initialize_build(self):
        try:
            # Always (re)select an active API key before building the service
            credential_manager.reactivate_keys()
            new_api_key = credential_manager.get_api_key(
                "youtube", test_func=self._test_api_key
            )

            if not new_api_key:
                raise Exception("No available YouTube API keys")

            self.api_key = new_api_key
            self._build = build(
                "youtube",
                "v3",
                developerKey=self.api_key,
            )
            # Log which API key is being used (masked for security)
            masked_key = (
                self.api_key[:10] + "..." + self.api_key[-10:]
                if len(self.api_key) > 20
                else self.api_key
            )
            self.logger.success(
                f"YouTube API service initialized with key: {masked_key}"
            )

        except Exception as e:
            self.logger.error(f"Failed to initialize YouTube service: {e}")
            raise

    def execute(self, factory: FunctionType, total_attempts: int = 3):
        """Execute an API request with automatic key rotation.

        Accepts either a pre-built `request` object or a `request_factory`
        callable. The callable should accept the current `build` service and
        return a fresh request. Using a factory is recommended so the request
        is rebuilt after key rotation.
        """

        for attempt in range(total_attempts):
            try:
                if not self._build:
                    self._initialize_build()

                # Build or reuse the request
                request = factory(self._build)

                return request.execute()

            except HttpError as e:
                if self._handle_api_error(e):
                    # Reset service to force re-initialization with a new key
                    self._build = None
                    self.logger.info(
                        f"Retrying with a different API key (attempt {attempt + 1}/{total_attempts})"
                    )
                    continue
                else:
                    # Re-raise non-retryable errors immediately
                    raise
            except Exception as e:
                self.logger.error(f"Unexpected error in API request: {e}")
                raise

        raise Exception("All API keys exhausted for YouTube API")

    def get_video_transcript(self, video_id: str, language_preference: list = None):
        """
        Get structured video transcript using native YouTube Captions API

        Args:
            video_id: YouTube video ID
            language_preference: List of preferred languages (default: ["en", "en-US", "en-GB"])

        Returns:
            Dictionary containing structured transcript data or None if failed
        """
        if not self.captions_api:
            self.logger.error("YouTube Captions API not initialized")
            return None

        try:
            response = self.captions_api.get_video_captions(
                video_id, language_preference or ["en", "en-US", "en-GB"]
            )

            if response.status_code == 200:
                return response.data
            else:
                self.logger.warning(
                    f"Failed to get transcript for {video_id}: {response.message}"
                )
                return None

        except Exception as e:
            self.logger.error(f"Error getting transcript for {video_id}: {e}")
            return None

    def list_video_captions(self, video_id: str):
        """
        List available caption tracks for a video

        Args:
            video_id: YouTube video ID

        Returns:
            Dictionary containing available captions information or None if failed
        """
        if not self.captions_api:
            self.logger.error("YouTube Captions API not initialized")
            return None

        try:
            response = self.captions_api.list_captions(video_id)

            if response.status_code == 200:
                return response.data
            else:
                self.logger.warning(
                    f"Failed to list captions for {video_id}: {response.message}"
                )
                return None

        except Exception as e:
            self.logger.error(f"Error listing captions for {video_id}: {e}")
            return None

    def download_specific_caption(self, caption_id: str, fmt: str = "ttml"):
        """
        Download a specific caption track

        Args:
            caption_id: Caption track ID
            fmt: Format for download ("ttml", "srt", "vtt")

        Returns:
            Dictionary containing caption data or None if failed
        """
        if not self.captions_api:
            self.logger.error("YouTube Captions API not initialized")
            return None

        try:
            response = self.captions_api.download_caption(caption_id, fmt)

            if response.status_code == 200:
                return response.data
            else:
                self.logger.warning(
                    f"Failed to download caption {caption_id}: {response.message}"
                )
                return None

        except Exception as e:
            self.logger.error(f"Error downloading caption {caption_id}: {e}")
            return None
