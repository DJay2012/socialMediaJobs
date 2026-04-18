from types import FunctionType
from typing import Any, Optional, List, Dict
from pymongo import MongoClient
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))
from log.logging import logger
from config.config import config
from classes.Youtube import Youtube

load_dotenv()

source_client = MongoClient(config.database.uri)
destination_client = MongoClient(config.database.uri_production)

# MongoDB connection setup
source_db = source_client["smFeeds"]
searchKeywords = source_db["searchKeywords"]
destination_db = destination_client["pnq"]
channelMaster = destination_db["channelMaster"]


class Channel:
    def __init__(self, data_source_type: str = "channelName"):
        """
        Initialize Channel class with configurable data source

        Args:
            data_source_type: Field name to look for in searchKeywords collection (default: "channelName")
        """
        self.youtube = Youtube()
        self.source_collection = searchKeywords
        self.destination_collection = channelMaster
        self.logger = logger
        self.data_source_type = data_source_type

    def get_channel_id_from_name(self, channel_name: str) -> Optional[str]:
        """
        Get channel ID for a given channel name using YouTube API search

        Args:
            channel_name: Name of the channel to search for

        Returns:
            Channel ID if found, None otherwise
        """
        try:
            response = self.youtube.execute(
                lambda svc: svc.search().list(
                    q=channel_name, part="snippet", type="channel", maxResults=1
                )
            )

            if response and "items" in response and response["items"]:
                channel_id = response["items"][0].get("id", {}).get("channelId")
                if channel_id:
                    self.logger.info(
                        f"Found channel ID for '{channel_name}': {channel_id}"
                    )
                    return channel_id

            self.logger.warning(f"Channel ID not found for '{channel_name}'")
            return None

        except Exception as e:
            self.logger.error(f"Error getting channel ID for {channel_name}: {e}")
            return None

    def get_channel_details(self, channel_ids: List[str]) -> List[Dict]:
        """
        Get detailed channel information for a list of channel IDs
        Processes channel IDs in chunks of 50 (YouTube API limit)

        Args:
            channel_ids: List of channel IDs to fetch details for

        Returns:
            List of channel detail dictionaries
        """
        if not channel_ids:
            self.logger.warning("No channel IDs provided")
            return []

        # YouTube API allows maximum 50 channel IDs per request
        CHUNK_SIZE = 50
        all_results = []

        try:
            # Process channel IDs in chunks of 50
            for i in range(0, len(channel_ids), CHUNK_SIZE):
                chunk = channel_ids[i : i + CHUNK_SIZE]
                self.logger.info(
                    f"Processing chunk {i//CHUNK_SIZE + 1}: {len(chunk)} channel IDs"
                )

                chunk_results = self._get_channel_details_chunk(chunk)
                all_results.extend(chunk_results)

            self.logger.info(
                f"Successfully processed {len(all_results)} channel details from {len(channel_ids)} IDs"
            )
            return all_results

        except Exception as e:
            self.logger.error(f"Error getting channel details: {e}")
            return []

    def _get_channel_details_chunk(self, channel_ids: List[str]) -> List[Dict]:
        """
        Get channel details for a single chunk of channel IDs (max 50)

        Args:
            channel_ids: List of channel IDs (max 50)

        Returns:
            List of channel detail dictionaries
        """
        try:
            channel_ids_str = ",".join(channel_ids)

            params = {
                "id": channel_ids_str,
                "part": "snippet,statistics,contentDetails",
            }

            response = self.youtube.execute(lambda svc: svc.channels().list(**params))

            if not response or "items" not in response:
                self.logger.warning(
                    f"No channel details found for chunk: {channel_ids}"
                )
                return []

            results = []
            for item in response["items"]:
                try:
                    snippet = item["snippet"]
                    statistics = item["statistics"]
                    content_details = item.get("contentDetails", {})

                    # Extract playlist ID (uploads playlist)
                    playlist_id = content_details.get("relatedPlaylists", {}).get(
                        "uploads", ""
                    )

                    channel_info = {
                        "channelId": item["id"],
                        "title": snippet["title"],
                        "description": snippet.get("description", ""),
                        "thumbnail": snippet.get("thumbnails", {})
                        .get("high", {})
                        .get("url", ""),
                        "subscribers": int(statistics.get("subscriberCount", 0)),
                        "videos": int(statistics.get("videoCount", 0)),
                        "views": int(statistics.get("viewCount", 0)),
                        "playlistId": playlist_id,
                    }

                    results.append(channel_info)
                    self.logger.info(
                        f"Processed channel details for: {snippet['title']}"
                    )

                except Exception as e:
                    self.logger.error(f"Error processing channel item: {e}")
                    continue

            self.logger.info(f"Chunk processed: {len(results)} channels")
            return results

        except Exception as e:
            self.logger.error(f"Error getting channel details for chunk: {e}")
            return []

    def store_channel_data(self, channel_details: List[Dict]) -> int:
        """
        Store channel data to channelMaster collection with upsert logic using bulk operations
        Only stores channelId, title (as channelName), and playlistId to searchKeywords
        Stores full channel details to channelMaster

        Args:
            channel_details: List of channel detail dictionaries

        Returns:
            Number of documents upserted
        """
        if not channel_details:
            self.logger.warning("No channel details provided for storage")
            return 0

        try:
            from pymongo import UpdateOne

            # Prepare bulk operations for searchKeywords collection
            search_keywords_operations = []
            channel_master_operations = []

            for channel in channel_details:
                # Prepare document for searchKeywords (only required fields)
                search_keywords_doc = {
                    "channelId": channel["channelId"],
                    "channelName": channel["title"],
                    "playlistId": channel["playlistId"],
                }

                # Add to bulk operations
                search_keywords_operations.append(
                    UpdateOne(
                        {"channelId": channel["channelId"]},
                        {"$set": search_keywords_doc},
                        upsert=True,
                    )
                )

                # Add full channel details to channelMaster
                channel_master_operations.append(
                    UpdateOne(
                        {"channelId": channel["channelId"]},
                        {"$set": channel},
                        upsert=True,
                    )
                )

            # Execute bulk operations for searchKeywords
            search_keywords_result = None
            if search_keywords_operations:
                search_keywords_result = self.source_collection.bulk_write(
                    search_keywords_operations, ordered=False
                )
                self.logger.info(
                    f"Search Keywords bulk operation: "
                    f"Inserted {search_keywords_result.upserted_count}, "
                    f"Modified {search_keywords_result.modified_count}, "
                    f"Matched {search_keywords_result.matched_count}"
                )

            # Execute bulk operations for channelMaster
            channel_master_result = None
            if channel_master_operations:
                channel_master_result = self.destination_collection.bulk_write(
                    channel_master_operations, ordered=False
                )
                self.logger.info(
                    f"Channel Master bulk operation: "
                    f"Inserted {channel_master_result.upserted_count}, "
                    f"Modified {channel_master_result.modified_count}, "
                    f"Matched {channel_master_result.matched_count}"
                )

            # Calculate total operations
            total_upserted = 0
            if search_keywords_result:
                total_upserted += (
                    search_keywords_result.upserted_count
                    + search_keywords_result.modified_count
                )
            if channel_master_result:
                total_upserted += (
                    channel_master_result.upserted_count
                    + channel_master_result.modified_count
                )

            # Log individual channel processing for visibility
            for channel in channel_details:
                self.logger.info(
                    f"Processed channel: {channel['title']} ({channel['channelId']})"
                )

            self.logger.info(f"Total bulk operations completed: {total_upserted}")
            return len(channel_details)  # Return number of channels processed

        except Exception as e:
            self.logger.error(f"Error storing channel data in bulk: {e}")
            # Fallback to individual operations if bulk fails
            self.logger.info("Falling back to individual operations...")
            return self._store_channel_data_individual(channel_details)

    def fetch_channels_from_mongo(self) -> List[str]:
        """
        Fetch channel names from searchKeywords collection based on data_source_type

        Returns:
            List of unique channel keys
        """
        try:
            # Find all documents where the specified field exists
            channels = self.source_collection.find(
                {self.data_source_type: {"$exists": True, "$ne": None}}
            )

            channel_output = []
            for channel in channels:
                key = channel.get(self.data_source_type, "").strip()
                if key and key not in channel_output:
                    channel_output.append(key)

            self.logger.info(
                f"Found {len(channel_output)} unique channel names from {self.data_source_type} field"
            )
            return channel_output

        except Exception as e:
            self.logger.error(f"Error fetching channels from MongoDB: {e}")
            return []

    def process_channels(self, channel_keys: List[str]) -> Dict[str, Any]:
        """
        Scenario 1: Process array of channel names directly
        1. Fetch channel IDs from YouTube API
        2. Get full channel details
        3. Store to channelMaster collection

        Args:
            channel_keys: List of channel key to process

        Returns:
            Dictionary with processing results
        """
        self.logger.info(
            f"Starting scenario 1: Processing {len(channel_keys)} {self.data_source_type}"
        )

        # Step 1: Get channel IDs for channel names
        channel_ids = [] if self.data_source_type == "channelName" else channel_keys
        failed_items = []

        if self.data_source_type == "channelName":
            for key in channel_keys:
                if not key or not key.strip():
                    continue

                channel_id = self.get_channel_id_from_name(key.strip())
                if channel_id:
                    channel_ids.append(channel_id)
                else:
                    failed_items.append(key)

        self.logger.info(
            f"Found {len(channel_ids)} channel IDs, {len(failed_items)} failed"
        )

        # Step 2: Get channel details
        if not channel_ids:
            self.logger.warning("No channel IDs found, cannot proceed")
            return {
                "success": False,
                "processed": 0,
                "failed_names": failed_items,
                "channel_details": [],
            }

        channel_details = self.get_channel_details(channel_ids)

        # Step 3: Store to channelMaster and searchKeywords collection
        stored_count = self.store_channel_data(channel_details)

        result = {
            "success": True,
            "processed": stored_count,
            "failed_names": failed_items,
        }

        self.logger.info(f"Scenario 1 completed: {stored_count} channels processed")
        return result

    def process_channels_from_database(self) -> Dict[str, Any]:
        """
        Scenario 2: Fetch channel names from searchKeywords collection and process them
        1. Fetch channel names from MongoDB collection
        2. Process same as scenario 1

        Returns:
            Dictionary with processing results
        """
        self.logger.info(
            f"Starting scenario 2: Fetching channels from {self.data_source_type} field"
        )

        # Step 1: Fetch channel names from database
        channel_keys = self.fetch_channels_from_mongo()

        if not channel_keys:
            self.logger.warning("No channel names found in database")
            return {
                "success": False,
                "processed": 0,
                "failed_names": [],
                "channel_details": [],
            }

        # Step 2: Process using scenario 1 logic
        return self.process_channels(channel_keys)


def main():
    """
    Main function for demonstration
    """
    logger.info("Starting Channel processing demonstration...")
    try:
        channel = Channel("channelId")
        channel.process_channels_from_database()
    except Exception as e:
        logger.error(f"Error in main execution: {e}")


if __name__ == "__main__":
    main()
