"""
YouTube BMW Scraper
Specialized scraper for BMW YouTube channel data collection
Based on the original BmwYoutube.py but improved
"""

from typing import Dict
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from youtube_transcript_api import YouTubeTranscriptApi

from classes.APIKeyManager import api_key_manager
from classes.BaseScraper import BaseScraper
from config.config import config


# YouTube BMW scraper for specific channel data collection
class YouTubeBmwScraper(BaseScraper):

    # Initialize YouTube BMW scraper
    def __init__(self):
        super().__init__("YouTube BMW")
        self.youtube_service = None

    # Get an API key with automatic rotation
    def _get_api_key(self) -> str:
        """Get an API key with automatic rotation"""
        # Check and reactivate keys if needed
        api_key_manager.check_and_reactivate_keys()

        # First try to get a working key by testing each one
        api_key = api_key_manager.get_working_api_key("youtube", self._test_api_key)

        if not api_key:
            # Fallback to round-robin strategy if no working key found
            api_key = api_key_manager.get_api_key("youtube", "round_robin")

        if not api_key:
            raise Exception("No available YouTube API keys")

        return api_key

    # Handle API errors and retry with different keys
    def _handle_api_error(self, error: HttpError, current_api_key: str = None):

        # Handle API errors and report them to the API key manager
        if error.resp.status == 403:
            # Check for quota exceeded
            if "quotaExceeded" in str(error) or "quota" in str(error).lower():
                self.logger.warning(
                    "YouTube API quota exceeded, reporting error to key manager"
                )
                if current_api_key:
                    api_key_manager.report_error(
                        "youtube", current_api_key, "quota_exceeded"
                    )
                return True  # Indicates we should retry with a different key
            # Check for blocked/forbidden requests
            elif "blocked" in str(error).lower() or "forbidden" in str(error).lower():
                self.logger.warning(
                    f"YouTube API request blocked for key, reporting error to key manager: {str(error)}"
                )
                if current_api_key:
                    api_key_manager.report_error(
                        "youtube", current_api_key, "invalid_key"
                    )
                return True  # Indicates we should retry with a different key
            # Generic 403 error
            else:
                self.logger.warning(
                    f"YouTube API 403 error, reporting error to key manager: {str(error)}"
                )
                if current_api_key:
                    api_key_manager.report_error(
                        "youtube", current_api_key, "invalid_key"
                    )
                return True
        elif error.resp.status == 401:
            self.logger.error(
                "YouTube API authentication failed, reporting invalid key"
            )
            if current_api_key:
                api_key_manager.report_error("youtube", current_api_key, "invalid_key")
            return True
        elif error.resp.status == 429:
            self.logger.warning(
                "YouTube API rate limit exceeded, reporting error to key manager"
            )
            if current_api_key:
                api_key_manager.report_error("youtube", current_api_key, "rate_limit")
            return True

        return False  # Don't retry for other errors

    # Execute API request with automatic key rotation on errors
    def _execute_with_retry(self, request_func, max_retries: int = 3):
        """Execute API request with automatic key rotation on quota/rate limit errors"""
        for attempt in range(max_retries):
            try:
                if not self.youtube_service:
                    self._initialize_youtube_service()

                return request_func()

            except HttpError as e:
                current_api_key = getattr(self, "_current_api_key", None)

                if self._handle_api_error(e, current_api_key):
                    # Reset service to force re-initialization with new key
                    self.youtube_service = None
                    self.logger.info(
                        f"Retrying with different API key (attempt {attempt + 1}/{max_retries})"
                    )
                    continue
                else:
                    # Re-raise non-retryable errors
                    raise
            except Exception as e:
                self.logger.error(f"Unexpected error in API request: {e}")
                raise

        raise Exception("All API keys exhausted for YouTube API")

    # Initialize YouTube API service
    def _initialize_youtube_service(self):
        try:
            api_key = self._get_api_key()
            self._current_api_key = api_key  # Store current API key for error reporting
            self.youtube_service = build(
                "youtube",
                "v3",
                developerKey=api_key,
            )
            # Log which API key is being used (masked for security)
            masked_key = (
                api_key[:10] + "..." + api_key[-10:] if len(api_key) > 20 else api_key
            )
            self.logger.success(
                f"YouTube API service initialized with key: {masked_key}"
            )
        except Exception as e:
            self.logger.error(f"Failed to initialize YouTube service: {e}")
            raise

    # Test API key validity with a simple request
    def _test_api_key(self, api_key: str) -> bool:
        """Test if an API key is valid and can make requests"""
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
                self.logger.warning(f"API key test failed with 403: {str(e)}")
                return False
            elif e.resp.status == 401:
                self.logger.warning(f"API key test failed with 401: {str(e)}")
                return False
            else:
                self.logger.warning(
                    f"API key test failed with status {e.resp.status}: {str(e)}"
                )
                return False
        except Exception as e:
            self.logger.warning(f"API key test failed with unexpected error: {str(e)}")
            return False

    # Get channel ID for a given channel name
    def get_channel_id(self, channel_name: str):
        def _make_request():
            if not self.youtube_service:
                self._initialize_youtube_service()

            print(self.youtube_service)
            request = self.youtube_service.search().list(
                q=channel_name, part="snippet", type="channel", maxResults=1
            )
            return request.execute()

        try:
            response = self._execute_with_retry(_make_request)

            if response["items"]:
                channel_id = response["items"][0]["snippet"]["channelId"]
                return channel_id
            else:
                self.logger.warning(f"Channel '{channel_name}' not found.")
                return None
        except Exception as e:
            self.logger.error(f"Error getting channel ID for {channel_name}: {e}")
            return None

    # Get all videos from a specific channel
    def get_channel_videos(self, channel_id: str):
        def _make_request(page_token=None):
            if not self.youtube_service:
                self._initialize_youtube_service()

            request_params = {
                "channelId": channel_id,
                "part": "snippet",
                "maxResults": 50,
                "order": "date",
            }
            if page_token:
                request_params["pageToken"] = page_token

            request = self.youtube_service.search().list(**request_params)
            return request.execute()

        try:
            videos = []
            response = self._execute_with_retry(lambda: _make_request())
            videos.extend(response["items"])

            # Handle pagination
            while "nextPageToken" in response:
                try:
                    response = self._execute_with_retry(
                        lambda: _make_request(response["nextPageToken"])
                    )
                    videos.extend(response["items"])
                except Exception as e:
                    self.logger.warning(f"Error during pagination: {e}")
                    break

            return videos
        except Exception as e:
            self.logger.error(f"Error getting channel videos: {e}")
            return []

    # Get video statistics and location
    def get_video_statistics(self, video_id: str):
        def _make_request():
            if not self.youtube_service:
                self._initialize_youtube_service()

            request = self.youtube_service.videos().list(
                part="statistics, recordingDetails", id=video_id
            )
            return request.execute()

        try:
            response = self._execute_with_retry(_make_request)

            if response["items"]:
                stats = response["items"][0]["statistics"]
                location = (
                    response["items"][0]
                    .get("recordingDetails", {})
                    .get("location", "No location available")
                )
                return stats, location
            else:
                return None, None
        except Exception as e:
            self.logger.error(f"Error getting video statistics for {video_id}: {e}")
            return None, None

    # Get video transcript
    def get_video_transcript(self, video_id: str):

        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            return transcript
        except Exception as e:
            return f"Transcript not available: {str(e)}"

    # Search for influencer content in a specific channel
    def search_influencer_in_channel(
        self, channel_name: str, influencer_name: str, client_info: dict
    ):

        try:
            if not self.youtube_service:
                self._initialize_youtube_service()

            channel_id = self.get_channel_id(channel_name)

            if not channel_id:
                return False

            videos = self.get_channel_videos(channel_id)

            # Filter videos containing influencer name
            filtered_videos = [
                video
                for video in videos
                if (
                    influencer_name.lower() in video["snippet"]["title"].lower()
                    or influencer_name.lower()
                    in video["snippet"]["description"].lower()
                )
            ]

            if not filtered_videos:
                self.logger.info(
                    f"No videos found for influencer '{influencer_name}' in channel '{channel_name}'"
                )
                return True

            collection = self.getCollection(config.database.collections["youtube"])

            for video in filtered_videos:
                try:
                    video_id = video["id"]["videoId"]
                    title = video["snippet"]["title"]
                    description = video["snippet"]["description"]
                    publish_date = video["snippet"]["publishedAt"]
                    thumbnail = video["snippet"]["thumbnails"]["high"]["url"]
                    video_link = f"https://www.youtube.com/watch?v={video_id}"

                    stats, location = self.get_video_statistics(video_id)
                    transcript = self.get_video_transcript(video_id)

                    youtube_data = {
                        "_id": video_id,
                        "channel_name": channel_name,
                        "influencer_name": influencer_name,
                        "video_title": title,
                        "video_description": description,
                        "createdAt": self.parsePublishedAt(publish_date),
                        "thumbnail_url": thumbnail,
                        "video_link": video_link,
                        "statistics": {
                            "view_count": stats.get("viewCount", "Not available"),
                            "like_count": stats.get("likeCount", "Not available"),
                            "comment_count": stats.get("commentCount", "Not available"),
                        },
                        "location": location,
                        "transcript": transcript,
                    }

                    # Add client tags
                    youtube_data = self.addClientTags(youtube_data, client_info)

                    # Check and update existing record
                    if self.checkAndUpdateExistingRecord(
                        collection, video_id, youtube_data
                    ):
                        self.logger.info(f"Processed video: {title}")

                except Exception as e:
                    self.logger.error(f"Error processing video {video_id}: {e}")
                    continue

            return True

        except Exception as e:
            self.logger.error(f"Error in search_influencer_in_channel: {e}")
            return False

    # Process a single search keyword for BMW channels
    def processSingleKeyword(self, keyword_data: Dict[str, str]) -> bool:

        try:
            channel_name = keyword_data.get("channel_name", "")
            influencer_name = keyword_data.get("influencer_name", "")

            if not channel_name or not influencer_name:
                self.logger.warning(
                    "Missing channel_name or influencer_name in keyword data"
                )
                return False

            # Prepare client info
            client_info = {
                "clientId": keyword_data.get("clientId", ""),
                "clientName": keyword_data.get("clientName", ""),
                "companyId": keyword_data.get("companyId", ""),
                "companyName": keyword_data.get("companyName", ""),
            }

            return self.search_influencer_in_channel(
                channel_name, influencer_name, client_info
            )

        except Exception as e:
            self.logger.error(f"Error processing BMW keyword: {e}")
            return False


# Main function to run the YouTube BMW scraper
def main():
    scraper = YouTubeBmwScraper()
    scraper.run("youtubeBmw")


if __name__ == "__main__":
    main()
