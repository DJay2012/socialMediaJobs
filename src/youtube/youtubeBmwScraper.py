"""
YouTube BMW Scraper
Specialized scraper for BMW YouTube channel data collection
Based on the original BmwYoutube.py but improved
"""

from typing import Dict, Optional
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from youtube_transcript_api import YouTubeTranscriptApi

from classes.BaseScraper import BaseScraper
from classes.Youtube import Youtube
from config.CredentialManager import credential_manager
from config.config import config


# YouTube BMW scraper for specific channel data collection
class YouTubeBmwScraper(BaseScraper):

    # Initialize YouTube BMW scraper
    def __init__(self):
        super().__init__("YouTube BMW")
        self.youtube = Youtube()

    # Get channel ID for a given channel name
    def get_channel_id(self, channel_name: str):

        try:
            response = self.youtube.execute(
                lambda svc: svc.search().list(
                    q=channel_name, part="snippet", type="channel", maxResults=1
                )
            )

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
    def get_channel_videos(self, channel_id: str, page_token: Optional[str] = None):

        try:
            params = {
                "channelId": channel_id,
                "part": "snippet",
                "maxResults": 50,
                "order": "date",
            }

            if page_token:
                params["pageToken"] = page_token

            videos = []
            response = self.youtube.execute(lambda svc: svc.search().list(**params))
            videos.extend(response["items"])

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
                    videos.extend(response.get("items", []))
                except Exception as e:
                    self.logger.warning(f"Error during pagination: {e}")
                    break

            return videos
        except Exception as e:
            self.logger.error(f"Error getting channel videos: {e}")
            return []

    # Get video statistics and location
    def get_video_statistics(self, video_id: str):

        try:
            response = self.youtube.execute(
                lambda svc: svc.videos().list(
                    part="statistics, recordingDetails", id=video_id
                )
            )

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
