"""
YouTube Search Scraper
General YouTube search scraper for keyword-based video collection
"""

import requests
from typing import Dict, List, Optional

from classes.APIKeyManager import api_key_manager
from classes.BaseScraper import BaseScraper
from config.config import config


class YouTubeSearchScraper(BaseScraper):
    """YouTube search scraper with API key rotation"""

    def __init__(self):
        super().__init__("YouTube Search")
        self.current_api_key = None

    def getApiKey(self) -> str:
        """Get an API key with automatic rotation"""
        # Check and reactivate keys if needed
        api_key_manager.checkAndReactivateKeys()

        # Get key using round-robin strategy
        apiKey = api_key_manager.getApiKey("youtube", "round_robin")

        if not apiKey:
            raise Exception("No available YouTube API keys")

        self.current_api_key = apiKey
        return apiKey

    def fetchYoutubeData(
        self, query: str, maxResults: int, pageToken: Optional[str] = None
    ) -> Optional[Dict]:
        """Fetch YouTube search data with API key rotation"""
        max_retries = 3

        for attempt in range(max_retries):
            try:
                api_key = self.getApiKey()

                url = "https://www.googleapis.com/youtube/v3/search"
                params = {
                    "part": "snippet",
                    "maxResults": maxResults,
                    "q": query,
                    "regionCode": "IN",
                    "key": api_key,
                }

                if pageToken:
                    params["pageToken"] = pageToken

                response = requests.get(url, params=params)

                if response.status_code == 200:
                    self.logger.debug(
                        f"Successfully fetched data with {api_key[:20]}..."
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
                            f"Quota exceeded for key {api_key[:20]}..., switching to next key"
                        )
                        api_key_manager.report_error(
                            "youtube", api_key, "quota_exceeded"
                        )
                    elif "keyInvalid" in error_reason:
                        self.logger.warning(
                            f"Invalid key {api_key[:20]}..., switching to next key"
                        )
                        api_key_manager.report_error("youtube", api_key, "invalid_key")
                    else:
                        self.logger.warning(
                            f"API error with key {api_key[:20]}...: {error_reason}"
                        )
                        api_key_manager.report_error("youtube", api_key, "rate_limit")

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
                if attempt == max_retries - 1:
                    return None
                continue

        self.logger.error("All API keys exhausted for YouTube search")
        return None

    def fetch_video_details(self, video_ids: List[str]) -> Optional[Dict]:
        """Fetch detailed video information with API key rotation"""
        max_retries = 3

        for attempt in range(max_retries):
            try:
                api_key = self.getApiKey()

                url = "https://www.googleapis.com/youtube/v3/videos"
                params = {
                    "part": "snippet,statistics,contentDetails",
                    "id": ",".join(video_ids),
                    "key": api_key,
                }

                response = requests.get(url, params=params)

                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 403:
                    error_data = response.json()
                    error_reason = (
                        error_data.get("error", {})
                        .get("errors", [{}])[0]
                        .get("reason", "unknown")
                    )

                    if "quotaExceeded" in error_reason:
                        api_key_manager.report_error(
                            "youtube", api_key, "quota_exceeded"
                        )
                    elif "keyInvalid" in error_reason:
                        api_key_manager.report_error("youtube", api_key, "invalid_key")
                    else:
                        api_key_manager.report_error("youtube", api_key, "rate_limit")

                    continue
                else:
                    self.logger.error(
                        f"Failed to retrieve video details: {response.status_code}"
                    )
                    return None

            except Exception as e:
                self.logger.error(
                    f"Error fetching video details (attempt {attempt + 1}): {e}"
                )
                if attempt == max_retries - 1:
                    return None
                continue

        return None

    def fetch_channel_details(self, channel_ids: List[str]) -> Optional[Dict]:
        """Fetch channel information with API key rotation"""
        max_retries = 3

        for attempt in range(max_retries):
            try:
                api_key = self.getApiKey()

                url = "https://www.googleapis.com/youtube/v3/channels"
                params = {
                    "part": "snippet,statistics",
                    "id": ",".join(channel_ids),
                    "key": api_key,
                }

                response = requests.get(url, params=params)

                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 403:
                    error_data = response.json()
                    error_reason = (
                        error_data.get("error", {})
                        .get("errors", [{}])[0]
                        .get("reason", "unknown")
                    )

                    if "quotaExceeded" in error_reason:
                        api_key_manager.report_error(
                            "youtube", api_key, "quota_exceeded"
                        )
                    elif "keyInvalid" in error_reason:
                        api_key_manager.report_error("youtube", api_key, "invalid_key")
                    else:
                        api_key_manager.report_error("youtube", api_key, "rate_limit")

                    continue
                else:
                    self.logger.error(
                        f"Failed to retrieve channel details: {response.status_code}"
                    )
                    return None

            except Exception as e:
                self.logger.error(
                    f"Error fetching channel details (attempt {attempt + 1}): {e}"
                )
                if attempt == max_retries - 1:
                    return None
                continue

        return None

    def processSingleKeyword(self, keywordData: Dict[str, str]) -> bool:
        """Process a single search keyword"""
        try:
            query = keywordData["query"]
            self.logger.info(f"Processing YouTube search query: {query}")

            collection = self.getCollection(config.database.collections["youtube"])
            page_token = None

            while True:
                # Fetch search data with retry logic
                searchData = self.retryWithBackoff(
                    self.fetchYoutubeData, query, config.app.max_results, page_token
                )

                if not searchData:
                    self.logger.warning(f"No search data returned for query: {query}")
                    break

                # Extract video and channel IDs
                videoIds = [
                    item["id"]["videoId"]
                    for item in searchData.get("items", [])
                    if item["id"]["kind"] == "youtube#video"
                ]
                channelIds = list(
                    set(
                        item["snippet"]["channelId"]
                        for item in searchData.get("items", [])
                    )
                )

                if not videoIds:
                    self.logger.info("No video IDs found in search results")
                    break

                # Fetch detailed information
                videoDetails = self.retryWithBackoff(self.fetch_video_details, videoIds)
                channelDetails = self.retryWithBackoff(
                    self.fetch_channel_details, channelIds
                )

                if not videoDetails or not channelDetails:
                    self.logger.warning("Failed to fetch video or channel details")
                    break

                # Process videos
                successCount = self._process_videos(
                    searchData, videoDetails, channelDetails, keywordData, collection
                )

                self.logger.info(f"Processed {successCount} videos for query: {query}")

                # Check for next page
                page_token = searchData.get("nextPageToken")
                if not page_token:
                    break

                # Rate limiting
                self.rateLimitDelay()

            return True

        except Exception as e:
            self.logger.error(
                f"Error processing keyword {keywordData.get('query', 'unknown')}: {e}"
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
    """Main function to run the YouTube search scraper"""
    scraper = YouTubeSearchScraper()
    scraper.run("youtube")


if __name__ == "__main__":
    main()
