"""
YouTube BMW Scraper
Specialized scraper for BMW YouTube channel data collection
Based on the original BmwYoutube.py but improved
"""

from typing import Any, Dict
from src.schema.SocialFeed import SocialFeedSchema
from src.schema.Youtube import VideoSchema
from src.classes.BaseScraper import BaseScraper
from src.classes.Youtube import Youtube, SEARCH_KIND
from src.classes.DataMigration import DataMigration
from src.config.config import config
from src.types.enums import Keyword, SocialFeedType
from src.utils.helper import request_delay


# YouTube BMW scraper for specific channel data collection
class YouTubeScraper(BaseScraper):

    # Initialize YouTube BMW scraper
    def __init__(self):
        super().__init__("YouTube")
        self.youtube = Youtube()

    def _get_tags(self, data: Dict[str, Any]):
        return [
            {
                "clientId": data.get("clientId", ""),
                "clientName": data.get("clientName", ""),
                "companyId": data.get("companyId", ""),
                "companyName": data.get("companyName", ""),
            }
        ]

    def _search_influencer(self, videos, influencerName):
        """Search for influencer content in videos"""
        matched_videos = {}

        if not influencerName:
            return matched_videos

        influencer_list = influencerName.split(",")

        for item in videos:
            try:
                kind = item.get("kind")

                video_id = (
                    item.get("id", {}).get("videoId")
                    if kind == SEARCH_KIND
                    else item.get("contentDetails", {}).get("videoId")
                )

                snippet = item["snippet"]
                title = snippet["title"].lower()
                description = snippet["description"].lower()

                if any(
                    influencer.lower() in title or influencer.lower() in description
                    for influencer in influencer_list
                ):
                    matched_videos[video_id] = snippet
            except Exception as e:
                self.logger.error(f"Error searching for influencer: {str(e)}")
                continue

        self.logger.info(
            f"Found {len(matched_videos)} matched videos for {influencerName}"
        )
        return matched_videos

    def _search_keywords(self, videos, keywords):
        """Search for keyword matches in videos"""
        matched_videos = {}

        if not keywords:
            return matched_videos

        keywords = set([keyword.lower() for keyword in keywords])

        for item in videos:
            try:
                kind = item.get("kind")

                video_id = (
                    item.get("id", {}).get("videoId")
                    if kind == SEARCH_KIND
                    else item.get("contentDetails", {}).get("videoId")
                )
                snippet = item.get("snippet", {})
                title = snippet.get("title", "").lower()
                description = snippet.get("description", "").lower()

                for keyword in keywords:
                    if keyword in title or keyword in description:
                        if video_id not in matched_videos:
                            matched_videos[video_id] = {
                                **snippet,
                                "keywords": [keyword],
                            }
                        else:
                            matched_videos[video_id]["keywords"].append(keyword)

            except Exception as e:
                self.logger.error(f"Error searching for keywords: {str(e)}")
                continue

        self.logger.info(f"Found {len(matched_videos)} matched videos for {keywords}")

        return matched_videos

    def _process_youtube_data(self, videos: Dict[str, Any], **extras):
        """Process YouTube data and return structured format"""
        processed_data = []
        video_ids = list(videos.keys())
        video_details = self.youtube.get_video_info(video_ids, format="dict")

        for video_id, video in videos.items():
            try:
                if video_id not in video_details:
                    self.logger.warning(f"Video details not found for {video_id}")
                    continue

                video_data = video_details[video_id]
                stats = video_data.get("statistics", {})
                recordingDetails = video_data.get("recordingDetails", {})
                location = recordingDetails.get("location", None)
                transcripts = self.youtube.get_transcript(video_id)

                video.update(
                    {
                        **video_data,
                        "stats": stats,
                        "location": location,
                        "transcripts": transcripts,
                        **extras,
                    }
                )

                processed_data.append(VideoSchema.from_api(video).to_dict())
            except Exception as e:
                self.logger.error(f"Error processing video {video_id}: {str(e)}")
                continue

        return processed_data

    # Search for influencer content in a specific channel
    def _search(self, data):

        try:

            search_type = next(
                (key.value for key in Keyword if data.get(key.value, "")), None
            )

            search_value = data.get(search_type, "")

            tags = self._get_tags(data)

            matched_videos = {}

            if search_type == Keyword.PLAYLIST:
                playlist_id = data.get("playlistId", "")
                videos = self.youtube.get_channel_playlist_items(playlist_id)

                influencer_videos = self._search_influencer(
                    videos, data.get("influencerName", "")
                )

                keywords_videos = self._search_keywords(
                    videos, data.get("keywords", "")
                )

                matched_videos.update(influencer_videos)
                matched_videos.update(keywords_videos)

            elif search_type == Keyword.QUERY:
                matched_videos = self.youtube.search_query(data.get("query", ""))

            if not matched_videos:
                self.logger.warning(
                    f"No videos found for {search_type} - {search_value}"
                )
                return True

            collection = self.get_collection(config.database.collections["youtube"])

            processed_data = self._process_youtube_data(matched_videos, tags=tags)
            self.bulk_insert_or_replace(collection, processed_data)

            return True

        except Exception as e:
            self.logger.error(f"Error in YoutubeScraper._search: {e}")
            return False

    # Process a single search keyword for BMW channels
    def process_keyword(self, data: Dict[str, Any]) -> bool:

        try:
            return self._search(data)

        except Exception as e:
            self.logger.error(f"Error processing BMW keyword: {e}")
            return False


# Main function to run the YouTube BMW scraper
def youtube_scraper(
    search: Dict[str, Any] = None,
    start_date: str = None,
    end_date: str = None,
):
    platform = SocialFeedType.YOUTUBE.value

    scraper = YouTubeScraper()
    if start_date and end_date:
        scraper.youtube.set_date_range(start_date, end_date)

    scraper.run(platform, search)

    migration = DataMigration(platform)

    # Migrate to youtube collection
    migration.migrate(
        source="youtube",
        target="youtube",
        start_date=start_date,
        end_date=end_date,
    )

    migration.set_config(
        source_uri=config.database.uri_production,
        target_uri=config.database.uri_production,
        source_db="pnq",
        target_db="pnq",
    )

    request_delay(2)

    # Migrate to socialFeed collection
    migration.migrate(
        source="youtube",
        target="socialFeed",
        start_date=start_date,
        end_date=end_date,
        validation_schema=SocialFeedSchema,
    )
