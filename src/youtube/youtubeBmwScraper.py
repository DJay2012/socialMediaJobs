"""
YouTube BMW Scraper
Specialized scraper for BMW YouTube channel data collection
Based on the original BmwYoutube.py but improved
"""

import sys
from pathlib import Path
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
import pytz
from datetime import datetime
import time
import random
from googleapiclient.errors import HttpError
from typing import Dict

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from baseSocialMediaScraper import BaseSocialMediaScraper
from config import config


class YouTubeBmwScraper(BaseSocialMediaScraper):
    """YouTube BMW scraper for specific channel data collection"""

    def __init__(self):
        super().__init__("YouTube BMW")
        self.youtube_service = None

    def _initialize_youtube_service(self):
        """Initialize YouTube API service"""
        try:
            self.youtube_service = build(
                "youtube", "v3", developerKey=config.api.youtube_api_key
            )
            self.logger.info("YouTube API service initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize YouTube service: {e}")
            raise

    def get_channel_id(self, channel_name: str):
        """Get channel ID for a given channel name"""
        try:
            if not self.youtube_service:
                self._initialize_youtube_service()

            request = self.youtube_service.search().list(
                q=channel_name, part="snippet", type="channel", maxResults=1
            )
            response = request.execute()

            if response["items"]:
                channel_id = response["items"][0]["snippet"]["channelId"]
                return channel_id
            else:
                self.logger.warning(f"Channel '{channel_name}' not found.")
                return None
        except Exception as e:
            self.logger.error(f"Error getting channel ID for {channel_name}: {e}")
            return None

    def get_channel_videos(self, channel_id: str):
        """Get all videos from a specific channel"""
        try:
            if not self.youtube_service:
                self._initialize_youtube_service()

            videos = []
            request = self.youtube_service.search().list(
                channelId=channel_id, part="snippet", maxResults=50, order="date"
            )
            response = request.execute()

            videos.extend(response["items"])

            # Handle pagination
            while "nextPageToken" in response:
                request = self.youtube_service.search().list(
                    channelId=channel_id,
                    part="snippet",
                    maxResults=50,
                    pageToken=response["nextPageToken"],
                    order="date",
                )
                response = request.execute()
                videos.extend(response["items"])

            return videos
        except Exception as e:
            self.logger.error(f"Error getting channel videos: {e}")
            return []

    def get_video_statistics(self, video_id: str):
        """Get video statistics and location"""
        try:
            if not self.youtube_service:
                self._initialize_youtube_service()

            request = self.youtube_service.videos().list(
                part="statistics, recordingDetails", id=video_id
            )
            response = request.execute()

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

    def get_video_transcript(self, video_id: str):
        """Get video transcript"""
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            return transcript
        except Exception as e:
            return f"Transcript not available: {str(e)}"

    def search_influencer_in_channel(
        self, channel_name: str, influencer_name: str, client_info: dict
    ):
        """Search for influencer content in a specific channel"""
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

            collection = self.get_collection(config.database.collections["youtube"])

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
                        "createdAt": self.parse_published_at(publish_date),
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

    def process_single_keyword(self, keyword_data: Dict[str, str]) -> bool:
        """Process a single search keyword for BMW channels"""
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


def main():
    """Main function to run the YouTube BMW scraper"""
    scraper = YouTubeBmwScraper()
    scraper.run("youtubeBmw")


if __name__ == "__main__":
    main()
