"""
YouTube Scraper
Improved YouTube scraper using the new configuration system
"""

import requests
import logging
from typing import Dict, List, Optional
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from classes.APIKeyManager import api_key_manager
from classes.BaseScraper import BaseScraper
from config.config import config


class YouTubeScraper(BaseScraper):
    """YouTube scraper with improved error handling and security"""

    def __init__(self):
        super().__init__("YouTube")
        self.youtube_service = None

    def getApiKey(self) -> str:
        """Get an API key with automatic rotation"""
        # Check and reactivate keys if needed
        api_key_manager.checkAndReactivateKeys()

        # Get key using round-robin strategy
        apiKey = api_key_manager.getApiKey("youtube", "round_robin")

        if not apiKey:
            raise Exception("No available YouTube API keys")

        return apiKey

    def initializeYoutubeService(self):
        """Initialize YouTube API service"""
        try:
            apiKey = self.getApiKey()
            self.youtube_service = build("youtube", "v3", developerKey=apiKey)
            self.logger.info("YouTube API service initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize YouTube service: {e}")
            raise

    def fetchYoutubeData(
        self, query: str, maxResults: int, pageToken: Optional[str] = None
    ) -> Optional[Dict]:
        """Fetch YouTube search data with API key rotation"""
        maxRetries = 3

        for attempt in range(maxRetries):
            try:
                apiKey = self.getApiKey()

                url = "https://www.googleapis.com/youtube/v3/search"
                params = {
                    "part": "snippet",
                    "maxResults": maxResults,
                    "q": query,
                    "regionCode": "IN",
                    "key": apiKey,
                }

                if pageToken:
                    params["pageToken"] = pageToken

                response = requests.get(url, params=params)

                if response.status_code == 200:
                    self.logger.debug(
                        f"Successfully fetched data with {apiKey[:20]}..."
                    )
                    return response.json()
                elif response.status_code == 403:
                    # Quota exceeded or API key issue
                    error_data = response.json()
                    error_reason = (
                        error_data.get("error", {})
                        .get("errors", [{}])[0]
                        .get("reason", "unknown")
                    )

                    if "quotaExceeded" in error_reason:
                        self.logger.warning(
                            f"Quota exceeded for key {apiKey[:20]}..., switching to next key"
                        )
                        api_key_manager.report_error(
                            "youtube", apiKey, "quota_exceeded"
                        )
                    elif "keyInvalid" in error_reason:
                        self.logger.warning(
                            f"Invalid key {apiKey[:20]}..., switching to next key"
                        )
                        api_key_manager.report_error("youtube", apiKey, "invalid_key")
                    else:
                        self.logger.warning(
                            f"API error with key {apiKey[:20]}...: {error_reason}"
                        )
                        api_key_manager.report_error("youtube", apiKey, "rate_limit")

                    # Try with next key
                    continue
                else:
                    self.logger.error(
                        f"Failed to retrieve YouTube data: {response.status_code}"
                    )
                    return None

            except Exception as e:
                self.logger.error(
                    f"Error fetching YouTube data (attempt {attempt + 1}): {e}"
                )
                if attempt == maxRetries - 1:
                    return None
                continue

        self.logger.error("All API keys exhausted for YouTube search")
        return None

    def fetch_video_details(self, video_ids: List[str]) -> Optional[Dict]:
        """Fetch detailed video information"""
        try:
            if not self.youtube_service:
                self.initializeYoutubeService()

            url = "https://www.googleapis.com/youtube/v3/videos"
            params = {
                "part": "snippet,statistics,contentDetails",
                "id": ",".join(video_ids),
                "key": config.api.youtube_api_key,
            }

            response = requests.get(url, params=params)

            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(
                    f"Failed to retrieve video details: {response.status_code}"
                )
                return None

        except Exception as e:
            self.logger.error(f"Error fetching video details: {e}")
            return None

    def fetch_channel_details(self, channel_ids: List[str]) -> Optional[Dict]:
        """Fetch channel information"""
        try:
            if not self.youtube_service:
                self.initializeYoutubeService()

            url = "https://www.googleapis.com/youtube/v3/channels"
            params = {
                "part": "snippet,statistics",
                "id": ",".join(channel_ids),
                "key": config.api.youtube_api_key,
            }

            response = requests.get(url, params=params)

            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(
                    f"Failed to retrieve channel details: {response.status_code}"
                )
                return None

        except Exception as e:
            self.logger.error(f"Error fetching channel details: {e}")
            return None

    def processSingleKeyword(self, keyword_data: Dict[str, str]) -> bool:
        """Process a single search keyword"""
        try:
            query = keyword_data["query"]
            self.logger.info(f"Processing YouTube query: {query}")

            collection = self.getCollection(config.database.collections["youtube"])
            page_token = None

            while True:
                # Fetch search data with retry logic
                search_data = self.retryWithBackoff(
                    self.fetchYoutubeData, query, config.app.max_results, page_token
                )

                if not search_data:
                    self.logger.warning(f"No search data returned for query: {query}")
                    break

                # Extract video and channel IDs
                video_ids = [
                    item["id"]["videoId"]
                    for item in search_data.get("items", [])
                    if item["id"]["kind"] == "youtube#video"
                ]
                channel_ids = list(
                    set(
                        item["snippet"]["channelId"]
                        for item in search_data.get("items", [])
                    )
                )

                if not video_ids:
                    self.logger.info("No video IDs found in search results")
                    break

                # Fetch detailed information
                video_details = self.retryWithBackoff(
                    self.fetch_video_details, video_ids
                )
                channel_details = self.retryWithBackoff(
                    self.fetch_channel_details, channel_ids
                )

                if not video_details or not channel_details:
                    self.logger.warning("Failed to fetch video or channel details")
                    break

                # Process videos
                success_count = self._process_videos(
                    search_data,
                    video_details,
                    channel_details,
                    keyword_data,
                    collection,
                )

                self.logger.info(f"Processed {success_count} videos for query: {query}")

                # Check for next page
                page_token = search_data.get("nextPageToken")
                if not page_token:
                    break

                # Rate limiting
                self.rateLimitDelay()

            return True

        except Exception as e:
            self.logger.error(
                f"Error processing keyword {keyword_data.get('query', 'unknown')}: {e}"
            )
            return False

    def _process_videos(
        self,
        search_data: Dict,
        video_details: Dict,
        channel_details: Dict,
        keyword_data: Dict,
        collection,
    ) -> int:
        """Process and save video data"""
        success_count = 0

        # Create channel info lookup
        channel_info = {}
        for channel in channel_details.get("items", []):
            channel_info[channel["id"]] = {
                "profile_image": channel["snippet"]["thumbnails"]["default"]["url"],
                "location": channel["snippet"].get("country", "Unknown"),
            }

        for item in search_data.get("items", []):
            if item["id"]["kind"] == "youtube#video":
                try:
                    video_id = item["id"]["videoId"]
                    video_info = next(
                        (
                            video
                            for video in video_details.get("items", [])
                            if video["id"] == video_id
                        ),
                        {},
                    )

                    # Prepare video data
                    video_data = {
                        "_id": video_id,
                        "id": video_id,
                        "snippet": item["snippet"],
                        "statistics": video_info.get("statistics", {}),
                        "video_link": f"https://www.youtube.com/watch?v={video_id}",
                        "keywords": keyword_data["query"],
                        "createdAt": self.parsePublishedAt(
                            item["snippet"]["publishedAt"]
                        ),
                    }

                    # Add channel information
                    channel_id = item["snippet"]["channelId"]
                    video_data["profile_image"] = channel_info.get(channel_id, {}).get(
                        "profile_image"
                    )
                    video_data["location"] = channel_info.get(channel_id, {}).get(
                        "location"
                    )

                    # Add client tags
                    video_data = self.addClientTags(video_data, keyword_data)

                    # Save to database
                    if self.checkAndUpdateExistingRecord(
                        collection, video_id, video_data
                    ):
                        success_count += 1

                except Exception as e:
                    self.logger.error(
                        f"Error processing video {item.get('id', {}).get('videoId', 'unknown')}: {e}"
                    )
                    continue

        return success_count


def main():
    """Main function to run the YouTube scraper"""
    scraper = YouTubeScraper()
    scraper.run("youtube")


if __name__ == "__main__":
    main()
