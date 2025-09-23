from types import FunctionType
from threading import Lock
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from src.log.logging import logger
from src.utils.helper import request_delay
from src.config.CredentialManager import credential_manager


class Youtube:

    def __init__(self):
        self.logger = logger
        self.api_key = None
        self.captions_api = None
        self._build = None
        self._build_lock = Lock()  # Thread safety for service initialization

        # Reactivate any keys that may have been deactivated
        credential_manager.reactivate_keys()

        # Check if we have any available keys
        if not credential_manager.get_key_status("youtube")["active_keys"]:
            raise Exception("No available YouTube API keys")

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

    def _initialize_build(self, force_new_key: bool = False):
        with self._build_lock:
            try:
                # Get next API key in round-robin fashion or reuse current key
                if force_new_key or not self.api_key:
                    credential_manager.reactivate_keys()
                    new_api_key = credential_manager.get_api_key(
                        "youtube", strategy="round_robin"
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

                return self._build

            except Exception as e:
                self.logger.error(f"Failed to initialize YouTube service: {e}")
                raise

    def execute(
        self,
        factory: FunctionType,
        total_attempts: int = len(credential_manager.get_api_keys("youtube")),
    ):
        """Execute an API request with automatic key rotation.

        Uses round-robin strategy to distribute requests evenly across all available API keys.
        Each request gets the next available API key in sequence to ensure equal quota utilization.
        """

        for attempt in range(total_attempts):
            try:
                # Always get next API key in round-robin fashion for each request
                # This ensures equal distribution of quota usage across all keys
                self._initialize_build(force_new_key=True)

                # Build the request with current service
                request = factory(self._build)

                # Execute and return the result
                result = request.execute()

                # Log successful request with key info for monitoring
                masked_key = (
                    self.api_key[:10] + "..." + self.api_key[-10:]
                    if len(self.api_key) > 20
                    else self.api_key
                )
                self.logger.success(f"API request successful with key: {masked_key}")

                return result

            except HttpError as e:
                if self._handle_api_error(e):
                    # Reset service to force re-initialization with a new key
                    self._build = None
                    self.api_key = None  # Clear current key to force new selection
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
            finally:
                request_delay()

        raise Exception("All API keys exhausted for YouTube API")

    def get_key_usage_stats(self):
        """Get current API key usage statistics"""
        return credential_manager.get_key_status("youtube")

    def get_current_key_info(self):
        """Get information about the currently selected API key"""
        if self.api_key:
            masked_key = (
                self.api_key[:10] + "..." + self.api_key[-10:]
                if len(self.api_key) > 20
                else self.api_key
            )
            return {"masked_key": masked_key, "full_key_length": len(self.api_key)}
        return None
