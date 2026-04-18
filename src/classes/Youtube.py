"""
YouTube API Operations Class
Centralized class for all YouTube-related operations and methods
"""

from types import FunctionType
from typing import Any, Dict, List, Optional, Union
import threading
from dateutil import parser

from src.classes.YoutubeApiClient import YoutubeApiClient
from src.classes.Transcript import Transcript
from src.schema.Youtube import VideoSchema
from src.utils.helper import get_today_start, get_today_end
from src.log.logging import logger

SEARCH_KIND = "youtube#searchResult"
VIDEO_KIND = "youtube#video"
PLAYLIST_ITEM_KIND = "youtube#playlistItem"
CHANNEL_KIND = "youtube#channel"


class Youtube:
    """
    Centralized YouTube operations class
    Contains all YouTube-related methods for API interactions
    """

    def __init__(self):
        self.logger = logger
        # Use thread-local storage for YouTube instances to ensure thread safety
        self.thread_local = threading.local()
        self.start_date = get_today_start()
        self.end_date = get_today_end()
        self.max_results = 50

    def set_date_range(self, start_date: str, end_date: str):
        """Set the date range for YouTube operations"""
        self.start_date = start_date
        self.end_date = end_date
        self.logger.info(f"Date range set to {self.start_date} - {self.end_date}")

    def _get_youtube_instance(self):
        """Get or create YouTube instance for current thread using thread-local storage"""
        if not hasattr(self.thread_local, "youtube"):
            self.thread_local.youtube = YoutubeApiClient()
        return self.thread_local.youtube

    def _pagination(
        self,
        fetch_func: FunctionType,
        filter_func: FunctionType = None,
        pagination: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Handle pagination for data fetching functions.

        Args:
            fetch_func: Function that makes API calls and returns response with 'items' and 'nextPageToken'
            filter_func: Optional function to filter items and control pagination
            **kwargs: Additional parameters to pass to fetch_func

        Returns:
            List of all items from all pages combined
        """

        all_items = []
        current_page_token = None
        self._stop_pagination = False  # Instance variable for pagination control

        try:
            while True:
                # Call the fetch function with current parameters
                response = fetch_func(current_page_token)

                if not response:
                    self.logger.warning("No response received from fetch function")
                    break

                if not pagination:
                    return response.get("items", [])

                # Extract items from current page
                page_items = response.get("items", [])

                if filter_func:
                    filtered_items = filter_func(page_items)
                    all_items.extend(filtered_items)
                else:
                    all_items.extend(page_items)

                # Check if pagination should stop
                if self._stop_pagination:
                    break

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

    def search_query(
        self, q: str, search_params: Dict[str, Any] = None, pagination: bool = True
    ):
        """Get YouTube search results for a query"""
        try:
            if search_params is None:
                search_params = {}

            # Define the fetch function for pagination
            api_params = {
                "q": q,
                "type": "video",
                "part": "snippet",
                "maxResults": self.max_results,
                "order": "relevance",
                "regionCode": "IN",
                "publishedAfter": self.start_date,
                "publishedBefore": self.end_date,
                **search_params,
            }

            def fetch_func(page_token=None):
                if page_token:
                    api_params["pageToken"] = page_token
                return self._get_youtube_instance().execute(
                    lambda svc: svc.search().list(**api_params)
                )

            # Use pagination function to get all results
            results = self._pagination(fetch_func, pagination=pagination)
            self.logger.info(f"Found {len(results)} matched videos for {q}")

            # Convert results to dictionary format
            video_type = api_params.get("type", "video")
            type_id = video_type + "Id"
            results = {item["id"][type_id]: item for item in results}

            return results
        except Exception as e:
            self.logger.error(f"Error getting youtube search: {e}")
            return []

    def get_channel_videos(
        self, channel_id: str, q: str = None, pagination: bool = True
    ):
        """Get all videos from a specific channel"""
        try:
            # Define the fetch function for pagination
            def fetch_func(page_token=None):
                params = {
                    "part": "snippet",
                    "order": "date",
                    "type": "video",
                    "channelId": channel_id,
                    "maxResults": self.max_results,
                    "publishedAfter": self.start_date,
                    "publishedBefore": self.end_date,
                }
                if q:
                    params["q"] = q
                if page_token:
                    params["pageToken"] = page_token

                return self._get_youtube_instance().execute(
                    lambda svc: svc.search().list(**params)
                )

            # Use pagination function to get all results
            results = self._pagination(fetch_func, pagination)
            self.logger.info(f"Found {len(results)} videos for {channel_id}")

            return results
        except Exception as e:
            self.logger.error(f"Error getting channel videos: {e}")
            return []

    def get_channel_playlist_items(self, playlist_id: str, pagination: bool = True):
        """
        Get ALL videos from a channel using the automatic 'uploads' playlist.
        This is more quota-efficient than search.list method.

        The 'uploads' playlist is automatically created by YouTube and contains
        EVERY video uploaded to the channel - not just manually created playlists.
        """
        try:
            # Step 1: Get videos from uploads playlist (1 unit per page)
            def fetch_func(page_token=None):
                params = {
                    "part": "snippet, contentDetails",
                    "playlistId": playlist_id,
                    "maxResults": self.max_results,
                }
                if page_token:
                    params["pageToken"] = page_token
                return self._get_youtube_instance().execute(
                    lambda svc: svc.playlistItems().list(**params)
                )

            def filter_func(items):
                """
                Filter items by date range and control pagination intelligently.

                Logic for videos in reverse chronological order (newest first):
                1. Skip videos newer than end_date (continue pagination)
                2. Include videos within [start_date, end_date]
                3. Stop when we find a video older than start_date

                Edge cases handled:
                - No videos in range across multiple pages
                - All videos too new (before finding range)
                - All videos too old (should not happen with newest-first order)
                - Empty pages
                - Invalid/missing dates on some videos
                - Date range spanning multiple pages
                """
                filtered_items = []

                # If no items, continue pagination (might be a gap)
                if not items:
                    return filtered_items

                # Track dates for debugging
                oldest_in_page = None
                newest_in_page = None

                for item in items:
                    snippet = item.get("snippet", {})
                    published_at = snippet.get("publishedAt", "")

                    # Skip items without published date
                    if not published_at:
                        self.logger.warning(
                            f"Video without publishedAt: {item.get('id')}"
                        )
                        continue

                    try:
                        # Parse the published date, start_date and end_date
                        pub_date = parser.isoparse(published_at)
                        start_dt = parser.isoparse(self.start_date)
                        end_dt = parser.isoparse(self.end_date)

                        # Track page boundaries for logging
                        if newest_in_page is None or pub_date > newest_in_page:
                            newest_in_page = pub_date
                        if oldest_in_page is None or pub_date < oldest_in_page:
                            oldest_in_page = pub_date

                        # Case 3: Both dates specified - the normal case
                        if pub_date > end_dt:
                            # Video is too new, skip but continue pagination
                            # This is common for the first few pages
                            continue
                        elif pub_date >= start_dt:
                            # Video is within range - this is what we want
                            filtered_items.append(item)
                            self._found_videos_in_range = True
                        else:
                            # Video is older than start_date
                            # Since videos are newest-first, all remaining will be older
                            self._gone_past_range = True
                            self._stop_pagination = True
                            break

                    except Exception as e:
                        self.logger.error(f"Error parsing date {published_at}: {e}")
                        continue

                # Intelligent pagination decision
                if not self._stop_pagination:
                    # Decide whether to continue pagination
                    if oldest_in_page and start_dt:
                        # If the oldest video on this page is still newer than start_date,
                        # we should continue pagination to find older videos
                        if oldest_in_page > start_dt:
                            # Continue pagination
                            pass
                        else:
                            # We've seen videos older than start_date
                            # If we haven't found any videos in range yet, stop
                            if not self._found_videos_in_range and filtered_items == []:
                                self._stop_pagination = True
                                self.logger.info(
                                    "No videos found in date range, stopping pagination"
                                )

                    # Safety check: if we've been paginating for too long without finding anything
                    # This prevents infinite pagination in edge cases
                    # (This would need a page counter implementation)

                return filtered_items

            # Use pagination to get all videos (date filtering is handled in filter_func)
            results = self._pagination(fetch_func, filter_func, pagination)

            self.logger.info(
                f"Found {len(results)} videos in playlist for {playlist_id} ID"
            )
            return results

        except Exception as e:
            self.logger.error(f"Error Youtube.get_channel_playlist_items: {e}")
            return []

    def get_channel_info(
        self, channel_ids: List[str], format: str = "list", pagination: bool = True
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Get channel info for a list of channel IDs"""
        try:
            channel_ids = ",".join(channel_ids)

            def fetch_func(page_token=None):
                params = {
                    "id": channel_ids,
                    "part": "snippet,statistics,contentDetails",  # Added contentDetails
                    "maxResults": self.max_results,
                }
                if page_token:
                    params["pageToken"] = page_token
                return self._get_youtube_instance().execute(
                    lambda svc: svc.channels().list(**params)
                )

            results = self._pagination(fetch_func, pagination)
            self.logger.info(
                f"Found {len(results)} channel info for {channel_ids.split(',')}"
            )

            if format == "dict":
                return {channel["id"]: channel for channel in results}

            return results

        except Exception as e:
            self.logger.error(f"Error getting channel info: {e}")
            return None

    def get_video_info(
        self, video_ids: List[str], format: str = "list", pagination: bool = True
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Get video info for a list of video IDs"""
        try:
            video_ids = ",".join(video_ids)

            def fetch_func(page_token=None):
                params = {
                    "part": "snippet,statistics,recordingDetails,contentDetails",
                    "id": video_ids,
                    "maxResults": self.max_results,
                }
                if page_token:
                    params["pageToken"] = page_token
                return self._get_youtube_instance().execute(
                    lambda svc: svc.videos().list(**params)
                )

            results = self._pagination(fetch_func, pagination)
            self.logger.info(
                f"Found {len(results)} video info for {video_ids.split(',')}"
            )

            if format == "dict":
                return {video["id"]: video for video in results}

            return results
        except Exception as e:
            self.logger.error(f"Error getting video info: {e}")
            return None

    def get_transcript(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Get transcript for a video"""
        transcripts = Transcript(video_id)
        return transcripts.fetch()
