"""
YouTube BMW Scraper
Specialized scraper for BMW YouTube channel data collection
Based on the original BmwYoutube.py but improved
"""

from types import FunctionType
from typing import Any, Dict, List, Optional, Tuple

from classes.BaseScraper import BaseScraper
from classes.Youtube import Youtube
from classes.Transcript import Transcript
from classes.DataMigration import DataMigration
from schema.Youtube import YoutubeSchema
from config.config import config
from enums.types import KeywordEntity, Platform
from utils.helper import get_today_start, get_today_end, request_delay


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

    def _get_client_info(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "clientId": data.get("clientId", ""),
            "clientName": data.get("clientName", ""),
            "companyId": data.get("companyId", ""),
            "companyName": data.get("companyName", ""),
        }

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
                response = fetch_func(
                    maxResults=max_results, pageToken=current_page_token, **kwargs
                )

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

                # Rate limiting delay between pages
                request_delay()

        except Exception as e:
            self.logger.error(f"Error during pagination: {e}")

        self.logger.info(
            f"Pagination completed. Total items collected: {len(all_items)}"
        )
        return all_items

    # * Youtube Methods
    # Get youtube search results
    def _search_query(self, q: str, type: str = "video", max_results: int = 50):

        try:
            # Define the fetch function for pagination
            def fetch_func(max_results):
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
                return self.youtube.execute(lambda svc: svc.search().list(**params))

            # Use pagination function to get all results
            results = self._pagination(fetch_func, max_results)

            return results
        except Exception as e:
            self.logger.error(f"Error getting youtube search: {e}")
            return []

    # Get all videos from a specific channel
    def _get_channel_videos(
        self, channel_id: str, q: str = None, max_results: int = 50
    ):

        try:
            # Define the fetch function for pagination
            def fetch_func(max_results):
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

                return self.youtube.execute(lambda svc: svc.search().list(**params))

            # Use pagination function to get all results
            results = self._pagination(fetch_func, max_results)

            return results
        except Exception as e:
            self.logger.error(f"Error getting channel videos: {e}")
            return []

    def _get_channel_info(self, channel_ids: List[str], max_results: int = 50):
        """Get channel info for a list of channel IDs"""
        try:
            channel_ids = ",".join(channel_ids)

            def fetch_func(max_results):
                params = {
                    "id": channel_ids,
                    "part": "snippet,statistics,recordingDetails",
                    "maxResults": max_results,
                }
                return self.youtube.execute(lambda svc: svc.channels().list(**params))

            results = self._pagination(fetch_func, max_results)
            return results

        except Exception as e:
            self.logger.error(f"Error getting channel info: {e}")
            return None

    def _get_video_info(self, video_ids: List[str], max_results: int = 50):
        """Get video info for a list of video IDs"""
        try:
            video_ids = ",".join(video_ids)

            def fetch_func(max_results):
                params = {
                    "part": "snippet,statistics,recordingDetails",
                    "id": video_ids,
                    "maxResults": max_results,
                }
                return self.youtube.execute(lambda svc: svc.videos().list(**params))

            results = self._pagination(fetch_func, max_results)
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

        return matched_videos

    def _process_youtube_data(self, videos):
        processed_data = []

        for video_id, data in videos.items():
            try:
                stats, location = self._get_video_statistics(video_id)
                transcripts = self._get_transcript(video_id)
                data.update(
                    {"stats": stats, "location": location, "transcripts": transcripts}
                )

                processed_data.append(YoutubeSchema(data))
            except Exception as e:
                self.logger.error(f"Error processing video {video_id}: {str(e)}")
                continue

        pass

    # Search for influencer content in a specific channel
    def _search(self, type: str, keyword: str, data):

        try:

            channel_name = data.get("channelName", "")
            channel_id = data.get("channelId", "")
            client_info = self._get_client_info(data)

            if type == KeywordEntity.INFLUENCER:
                videos = self._get_channel_videos(channel_id)
                matched_videos = self._search_influencer(videos, keyword)

            elif type == KeywordEntity.KEYWORDS:
                videos = self._get_channel_videos(channel_id)
                matched_videos = self._search_keywords(videos, keyword)

            elif type == KeywordEntity.QUERY:
                matched_videos = self._search_query(keyword)

            if not matched_videos:
                self.logger.info(f"No videos found for {type} with keyword '{keyword}'")
                return True

            collection = self.get_collection(config.database.collections["bmw"])

            for video in matched_videos:
                try:
                    video_id = video["id"]["videoId"]
                    title = video["snippet"]["title"]
                    description = video["snippet"]["description"]
                    publish_date = video["snippet"]["publishedAt"]
                    thumbnail = video["snippet"]["thumbnails"]["high"]["url"]
                    video_link = f"https://www.youtube.com/watch?v={video_id}"

                    stats, location = self._get_video_statistics(video_id)
                    stats = stats or {}
                    transcripts = self._get_transcript(video_id)

                    youtube_data = {
                        "_id": video_id,
                        "channelId": channel_id,
                        "channelName": channel_name,
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

    def _search_keywords_in_channel(self, data):

        try:
            channel_id = data.get("channelId", "")
            keywords = data.get("keywords", [])
            client_info = self._get_client_info(data)
            channelName = data.get("channelName", "")

            # Validate inputs
            if not channel_id or not isinstance(keywords, list) or len(keywords) == 0:
                self.logger.warning("Missing channelName or keywords for search")
                return False

            # Use get_channel_videos to search within the channel for each keyword
            # Aggregate unique matches and track which keywords matched
            videos = self._get_channel_videos(channel_id, q=keywords)

            matched_videos = self._search_keywords(videos, keywords)

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

                    stats, location = self._get_video_statistics(video_id)
                    stats = stats or {}
                    transcripts = self._get_transcript(video_id)

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
    def process_keyword(self, data: Dict[str, Any]) -> bool:

        try:
            type = next((key for key in list(KeywordEntity) if key in data), None)
            keyword = data.get(type, None)

            if not keyword:
                self.logger.warning(f"Missing {type} in search keyword data")
                return False

            return self._search(type, keyword, data)

        except Exception as e:
            self.logger.error(f"Error processing BMW keyword: {e}")
            return False
        finally:
            request_delay()


# Main function to run the YouTube BMW scraper
def main():

    start_date = "2025-09-15T00:00:00Z"
    end_date = "2025-09-18T23:59:59Z"

    scraper = YouTubeBmwScraper()
    scraper.set_date_range(start_date, end_date)
    scraper.run("youtubeBmw")

    migration = DataMigration(Platform.YOUTUBE)
    migration.migrate(
        source="bmw",
        destination="youtube",
        start_date=start_date,
        end_date=end_date,
    )


if __name__ == "__main__":
    main()
