"""
YouTube BMW Scraper
Specialized scraper for BMW YouTube channel data collection
Based on the original BmwYoutube.py but improved
"""

from typing import Any, Dict, List, Optional, Tuple

from classes.BaseScraper import BaseScraper
from classes.Youtube import Youtube
from config.config import config
from types.types import SearchBy
from utils.helper import get_today_start, get_today_end, request_delay
from classes.Transcript import Transcript


# YouTube BMW scraper for specific channel data collection
class YouTubeBmwScraper(BaseScraper):

    # Initialize YouTube BMW scraper
    def __init__(self):
        super().__init__("YouTube BMW")
        self.youtube = Youtube()
        self.start_date = get_today_start()
        self.end_date = get_today_end()

    def set_date_range(self, start_date: str, end_date: str):
        self.start_date = start_date
        self.end_date = end_date

    # Get channel ID for a given channel name
    def get_channel_id(self, channelName: str) -> Optional[str]:
        """Get channel ID for a given channel name"""
        try:
            response = self.youtube.execute(
                lambda svc: svc.search().list(
                    q=channelName, part="snippet", type="channel", maxResults=1
                )
            )

            if response and "items" in response and response["items"]:
                # Per YouTube Data API, channel id is under id.channelId for search results
                channel_id = response["items"][0].get("id", {}).get("channelId")
                if channel_id:
                    self.logger.info(
                        f"Found channel ID for '{channelName}': {channel_id}"
                    )
                    return channel_id

            else:
                self.logger.warning(
                    f"Channel ID not found in response for '{channelName}'"
                )
                return None
        except Exception as e:
            self.logger.error(f"Error getting channel ID for {channelName}: {e}")
            return None

    # Get all videos from a specific channel
    def get_channel_videos(
        self, channel_id: str, q: str = None, page_token: Optional[str] = None
    ):

        try:
            params = {
                "channelId": channel_id,
                "part": "snippet",
                "maxResults": 50,
                "order": "date",
                "type": "video",
                "publishedAfter": self.start_date,
                "publishedBefore": self.end_date,
            }

            if q:
                params["q"] = q

            if page_token:
                params["pageToken"] = page_token

            videos = []
            response = self.youtube.execute(lambda svc: svc.search().list(**params))
            videos.extend(
                [
                    item
                    for item in response.get("items", [])
                    if item.get("id", {}).get("videoId")
                ]
            )

            # Handle pagination
            while True:
                next_token = response.get("nextPageToken")
                if not next_token:
                    break
                params["pageToken"] = next_token
                try:
                    response = self.youtube.execute(
                        lambda svc: svc.search().list(**params)
                    )
                    videos.extend(
                        [
                            item
                            for item in response.get("items", [])
                            if item.get("id", {}).get("videoId")
                        ]
                    )
                except Exception as e:
                    self.logger.warning(f"Error during pagination: {e}")
                    break

            return videos
        except Exception as e:
            self.logger.error(f"Error getting channel videos: {e}")
            return []

    def get_transcript(self, video_id: str) -> Optional[Dict[str, Any]]:
        transcripts = Transcript(video_id)
        return transcripts.fetch()

    # Get video statistics and location
    def get_video_statistics(
        self, video_id: str
    ) -> Tuple[Optional[Dict], Optional[str]]:
        """Get video statistics and location"""
        try:
            response = self.youtube.execute(
                lambda svc: svc.videos().list(
                    part="statistics, recordingDetails", id=video_id
                )
            )

            if response and "items" in response and response["items"]:
                video_data = response["items"][0]
                stats = video_data.get("statistics", {})
                location = video_data.get("recordingDetails", {}).get("location", None)
                return stats, location
            else:
                self.logger.warning(f"No statistics data found for video {video_id}")
                return None, None
        except Exception as e:
            self.logger.error(f"Error getting video statistics for {video_id}: {e}")
            return None, None

    # Search for influencer content in a specific channel
    def search_influencer_in_channel(
        self, channelName: str, influencerName: str, client_info: dict
    ):

        try:

            channel_id = self.get_channel_id(channelName)

            if not channel_id:
                return False

            videos = self.get_channel_videos(channel_id)

            # Filter videos containing influencer name
            filtered_videos = []
            for video in videos:
                try:
                    title = video["snippet"]["title"].lower()
                    description = video["snippet"].get("description", "").lower()
                    if (
                        influencerName.lower() in title
                        or influencerName.lower() in description
                    ):
                        filtered_videos.append(video)
                except Exception:
                    continue

            if not filtered_videos:
                self.logger.info(
                    f"No videos found for influencer '{influencerName}' in channel '{channelName}'"
                )
                return True

            collection = self.get_collection(config.database.collections["bmw"])

            for video in filtered_videos:
                try:
                    video_id = video["id"]["videoId"]
                    title = video["snippet"]["title"]
                    description = video["snippet"]["description"]
                    publish_date = video["snippet"]["publishedAt"]
                    thumbnail = video["snippet"]["thumbnails"]["high"]["url"]
                    video_link = f"https://www.youtube.com/watch?v={video_id}"

                    stats, location = self.get_video_statistics(video_id)
                    stats = stats or {}
                    transcripts = self.get_transcript(video_id)

                    youtube_data = {
                        "_id": video_id,
                        "channelId": channel_id,
                        "channelName": channelName,
                        "title": title,
                        "description": description,
                        "publishedAt": (
                            self.parse_published_at(publish_date)
                            if publish_date
                            else None
                        ),
                        "thumbnail": thumbnail,
                        "videoLink": video_link,
                        "statistics": {
                            "views": stats.get("viewCount", None),
                            "likes": stats.get("likeCount", None),
                            "comments": stats.get("commentCount", None),
                        },
                        "location": location,
                        "transcripts": transcripts,
                    }

                    # Add client tags
                    youtube_data = self.add_client_tags(youtube_data, client_info)

                    # Check and update existing record
                    if self.check_and_update_existing_record(
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
        finally:
            request_delay()

    def search_keywords_in_channel(
        self, channelName: str, keywords: List[str], client_info: Dict
    ):

        try:

            # Validate inputs
            if not channelName or not isinstance(keywords, list) or len(keywords) == 0:
                self.logger.warning("Missing channelName or keywords for search")
                return False

            channel_id = self.get_channel_id(channelName)

            if not channel_id:
                return False

            # Use get_channel_videos to search within the channel for each keyword
            # Aggregate unique matches and track which keywords matched
            matched_videos = {}

            for keyword in keywords:
                if not keyword:
                    continue

                try:
                    videos = self.get_channel_videos(channel_id, q=keyword)
                except Exception as e:
                    self.logger.warning(
                        f"Channel videos retrieval failed for keyword '{keyword}': {e}"
                    )
                    continue

                for item in videos:
                    video_id = item.get("id", {}).get("videoId")
                    if not video_id:
                        continue

                    if video_id not in matched_videos:
                        matched_videos[video_id] = {
                            "snippet": item.get("snippet", {}),
                            "matched_keywords": set([keyword]),
                        }
                    else:
                        matched_videos[video_id]["matched_keywords"].add(keyword)

            if not matched_videos:
                self.logger.info(
                    f"No videos found for keywords {keywords} in channel '{channelName}'"
                )
                return True

            collection = self.get_collection(config.database.collections["bmw"])

            for video_id, data in matched_videos.items():
                try:
                    snippet = data.get("snippet", {})
                    title = snippet.get("title", "")
                    description = snippet.get("description", "")
                    publish_date = snippet.get("publishedAt", "")
                    thumbnails = snippet.get("thumbnails", {})
                    thumbnail = (
                        thumbnails.get("high", {}).get("url")
                        or thumbnails.get("medium", {}).get("url")
                        or thumbnails.get("default", {}).get("url")
                        or ""
                    )
                    video_link = f"https://www.youtube.com/watch?v={video_id}"

                    stats, location = self.get_video_statistics(video_id)
                    stats = stats or {}
                    transcripts = self.get_transcript(video_id)

                    youtube_data = {
                        "_id": video_id,
                        "channelId": channel_id,
                        "channelName": channelName,
                        "title": title,
                        "description": description,
                        "publishedAt": (
                            self.parse_published_at(publish_date)
                            if publish_date
                            else None
                        ),
                        "thumbnail": thumbnail,
                        "videoLink": video_link,
                        "statistics": {
                            "views": stats.get("viewCount", None),
                            "likes": stats.get("likeCount", None),
                            "comments": stats.get("commentCount", None),
                        },
                        "location": location,
                        "transcripts": transcripts,
                        "matchedKeywords": sorted(
                            list(data.get("matched_keywords", []))
                        ),
                    }

                    # Add client tags
                    youtube_data = self.add_client_tags(youtube_data, client_info)

                    # Check and update existing record
                    if self.check_and_update_existing_record(
                        collection, video_id, youtube_data
                    ):
                        self.logger.info(f"Processed video: {title}")

                except Exception as e:
                    self.logger.error(f"Error processing video {video_id}: {e}")
                    continue

            return True

        except Exception as e:
            self.logger.error(f"Error in search_keywords_in_channel: {e}")
            return False
        finally:
            request_delay()

    # Process a single search keyword for BMW channels
    def process_single_keyword(self, keyword_data: Dict[str, Any]) -> bool:

        try:
            channelName = keyword_data.get("channelName", "")
            influencerName = keyword_data.get("influencerName", "")
            keywords = keyword_data.get("keywords", [])

            if not channelName:
                self.logger.warning("Missing channelName in keyword data")
                return False

            # Prepare client info
            client_info = {
                "clientId": keyword_data.get("clientId", ""),
                "clientName": keyword_data.get("clientName", ""),
                "companyId": keyword_data.get("companyId", ""),
                "companyName": keyword_data.get("companyName", ""),
            }

            if influencerName:
                return self.search_influencer_in_channel(
                    channelName, influencerName, client_info
                )
            elif keywords:
                return self.search_keywords_in_channel(
                    channelName, keywords, client_info
                )

            else:
                self.logger.warning(
                    "Missing influencerName or keywords in keyword data"
                )
                return False

        except Exception as e:
            self.logger.error(f"Error processing BMW keyword: {e}")
            return False


# Main function to run the YouTube BMW scraper
def main():
    scraper = YouTubeBmwScraper()
    scraper.set_date_range("2025-08-01T00:00:00Z", "2025-08-31T23:59:59Z")
    scraper.run("youtubeBmw", SearchBy.KEYWORDS, 10)


if __name__ == "__main__":
    main()
