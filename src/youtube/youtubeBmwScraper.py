"""
YouTube BMW Scraper
Specialized scraper for BMW YouTube channel data collection
Based on the original BmwYoutube.py but improved
"""

from types import FunctionType
from typing import Any, Dict, List, Optional, Tuple, Union

from classes.BaseScraper import BaseScraper
from classes.Youtube import Youtube
from classes.Transcript import Transcript
from classes.DataMigration import DataMigration
from schema.Youtube import YoutubeSchema
from config.config import config
from enums.types import KeywordEntity, Platform
from utils.helper import get_today_start, get_today_end


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

    # Pagination handler for data fetching functions
    def _pagination(
        self,
        fetch_func: FunctionType,
        max_results: int = 50,
        page_token: Optional[str] = None,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """
        Handle pagination for data fetching functions.

        Args:
            fetch_func: Function that makes API calls and returns response with 'items' and 'nextPageToken'
            max_results: Maximum results per page (default: 50)
            page_token: Starting page token (optional)
            **kwargs: Additional parameters to pass to fetch_func

        Returns:
            List of all items from all pages combined
        """
        all_items = []
        current_page_token = page_token

        try:
            while True:
                # Call the fetch function with current parameters
                response = fetch_func(max_results, current_page_token)

                if not response:
                    self.logger.warning("No response received from fetch function")
                    break

                # Extract items from current page
                page_items = response.get("items", [])
                if page_items:
                    all_items.extend(page_items)

                # Check for next page
                next_page_token = response.get("nextPageToken")
                if not next_page_token:
                    break

                current_page_token = next_page_token

        except Exception as e:
            self.logger.error(f"Error during pagination: {e}")

        self.logger.info(
            f"Pagination completed. Total items collected: {len(all_items)}"
        )
        return all_items

    # * Youtube Methods
    # Get youtube search results
    def _search_query(self, q: str, type: str = "video", max_results: int = 100):

        try:
            # Define the fetch function for pagination
            def fetch_func(max_results, page_token=None):
                params = {
                    "q": q,
                    "type": type,
                    "part": "snippet",
                    "maxResults": max_results,
                    "order": "relevance",
                    "regionCode": "IN",
                    "publishedAfter": self.start_date,
                    "publishedBefore": self.end_date,
                }
                if page_token:
                    params["pageToken"] = page_token
                return self.youtube.execute(lambda svc: svc.search().list(**params))

            # Use pagination function to get all results
            results = self._pagination(fetch_func, max_results)
            self.logger.info(f"Found {len(results)} matched videos for {q}")

            type_id = type + "Id"
            results = {item["id"][type_id]: item for item in results}

            return results
        except Exception as e:
            self.logger.error(f"Error getting youtube search: {e}")
            return []

    # Get all videos from a specific channel
    def _get_channel_videos(
        self, channel_id: str, q: str = None, max_results: int = 100
    ):

        try:
            # Define the fetch function for pagination
            def fetch_func(max_results, page_token=None):
                params = {
                    "part": "snippet",
                    "order": "date",
                    "type": "video",
                    "channelId": channel_id,
                    "maxResults": max_results,
                    "publishedAfter": self.start_date,
                    "publishedBefore": self.end_date,
                }
                if q:
                    params["q"] = q
                if page_token:
                    params["pageToken"] = page_token

                return self.youtube.execute(lambda svc: svc.search().list(**params))

            # Use pagination function to get all results
            results = self._pagination(fetch_func, max_results)
            self.logger.info(f"Found {len(results)} videos for {channel_id}")

            return results
        except Exception as e:
            self.logger.error(f"Error getting channel videos: {e}")
            return []

    def _get_channel_info(self, channel_ids: List[str], max_results: int = 100):
        """Get channel info for a list of channel IDs"""
        try:
            channel_ids = ",".join(channel_ids)

            def fetch_func(max_results, page_token=None):
                params = {
                    "id": channel_ids,
                    "part": "snippet,statistics,recordingDetails",
                    "maxResults": max_results,
                }
                if page_token:
                    params["pageToken"] = page_token
                return self.youtube.execute(lambda svc: svc.channels().list(**params))

            results = self._pagination(fetch_func, max_results)
            self.logger.info(
                f"Found {len(results)} channel info for {channel_ids.split(',')}"
            )

            return results

        except Exception as e:
            self.logger.error(f"Error getting channel info: {e}")
            return None

    def _get_video_info(
        self, video_ids: List[str], max_results: int = 100, format: str = "list"
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Get video info for a list of video IDs"""

        try:
            video_ids = ",".join(video_ids)

            def fetch_func(max_results, page_token=None):
                params = {
                    "part": "snippet,statistics,recordingDetails,contentDetails",
                    "id": video_ids,
                    "maxResults": max_results,
                }
                if page_token:
                    params["pageToken"] = page_token
                return self.youtube.execute(lambda svc: svc.videos().list(**params))

            results = self._pagination(fetch_func, max_results)
            self.logger.info(
                f"Found {len(results)} video info for {video_ids.split(',')}"
            )

            if format == "dict":
                return {video["id"]: video for video in results}

            return results
        except Exception as e:
            self.logger.error(f"Error getting video info: {e}")
            return None

    def _get_transcript(self, video_id: str) -> Optional[Dict[str, Any]]:
        transcripts = Transcript(video_id)
        return transcripts.fetch()

    def _search_influencer(self, videos, influencerName):
        matched_videos = {}
        influencerName = influencerName.lower()

        for item in videos:
            try:
                video_id = item["id"]["videoId"]
                snippet = item["snippet"]
                title = snippet["title"].lower()
                description = snippet["description"].lower()

                if influencerName in title or influencerName in description:
                    matched_videos[video_id] = snippet
            except Exception:
                continue

        self.logger.info(
            f"Found {len(matched_videos)} matched videos for {influencerName}"
        )
        return matched_videos

    def _search_keywords(self, videos, keywords):
        matched_videos = {}
        keywords = set([keyword.lower() for keyword in keywords])

        for item in videos:
            try:
                video_id = item.get("id", {}).get("videoId")
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

            except Exception:
                continue

        self.logger.info(f"Found {len(matched_videos)} matched videos for {keywords}")

        return matched_videos

    def _process_youtube_data(self, videos: Dict[str, Any], **extras):
        processed_data = []
        video_ids = list(videos.keys())
        video_details = self._get_video_info(video_ids, format="dict")

        for video_id, video in videos.items():
            try:
                if video_id not in video_details:
                    self.logger.warning(f"Video details not found for {video_id}")
                    continue

                video_data = video_details[video_id]
                stats = video_data.get("statistics", {})
                recordingDetails = video_data.get("recordingDetails", {})
                location = recordingDetails.get("location", None)
                transcripts = self._get_transcript(video_id)

                video.update(
                    {
                        **video_data,
                        "stats": stats,
                        "location": location,
                        "transcripts": transcripts,
                        **extras,
                    }
                )

                processed_data.append(YoutubeSchema.from_api(video).to_dict())
            except Exception as e:
                self.logger.error(f"Error processing video {video_id}: {str(e)}")
                continue

        return processed_data

    # Search for influencer content in a specific channel
    def _search(self, search_type: str, search_keyword: str, data):

        try:

            channel_id = data.get("channelId", "")
            company_tag = [
                {"id": data.get("companyId", ""), "name": data.get("companyName", "")}
            ]

            if search_type == KeywordEntity.INFLUENCER:
                videos = self._get_channel_videos(channel_id)
                matched_videos = self._search_influencer(videos, search_keyword)

            elif search_type == KeywordEntity.KEYWORDS:
                videos = self._get_channel_videos(channel_id)
                matched_videos = self._search_keywords(videos, search_keyword)

            elif search_type == KeywordEntity.QUERY:
                matched_videos = self._search_query(search_keyword)

            if not matched_videos:
                self.logger.warning(
                    f"No videos found for {search_type}: {search_keyword}"
                )
                return True

            collection = self.get_collection(config.database.collections["bmw"])

            processed_data = self._process_youtube_data(
                matched_videos, company_tag=company_tag
            )
            self.bulk_insert_or_replace(collection, processed_data)

            return True

        except Exception as e:
            self.logger.error(f"Error in YoutubeScraper._search: {e}")
            return False

    # Process a single search keyword for BMW channels
    def process_keyword(self, data: Dict[str, Any]) -> bool:

        try:
            search_type = None

            for key in KeywordEntity:
                if key.value in data and data[key.value] is not None:
                    search_type = key.value
                    break

            search_keyword = data.get(search_type, None)

            if not search_keyword or not search_type:
                self.logger.warning(f"Missing {search_type} in search keyword data")
                return False

            return self._search(search_type, search_keyword, data)

        except Exception as e:
            self.logger.error(f"Error processing BMW keyword: {e}")
            return False


# Main function to run the YouTube BMW scraper
def main():

    start_date = "2025-09-01T00:00:00Z"
    end_date = "2025-09-21T23:59:59Z"

    scraper = YouTubeBmwScraper()
    scraper.set_date_range(start_date, end_date)
    scraper.run("youtubeBmw", search_by={"channelName": "Autocar"})

    # migration = DataMigration(Platform.YOUTUBE)
    # migration.migrate(
    #     source="bmw",
    #     destination="youtube",
    #     start_date=start_date,
    #     end_date=end_date,
    # )


if __name__ == "__main__":
    main()
