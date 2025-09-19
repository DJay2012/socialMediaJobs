from typing import Optional, List, Dict
from pymongo import MongoClient

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))
from log.logging import logger
from classes.Youtube import Youtube

# MongoDB connection setup
client = MongoClient("mongodb://admin:Cir%5EPnq%406A@51.195.235.59:27017/")
db = client["smFeeds"]
collection = db["searchKeywords"]


def fetch_channels_from_mongo() -> List[Dict]:
    """
    Fetch all documents from MongoDB where channelName field exists
    Returns list of documents with channelName
    """
    try:
        # Find all documents where channelName field exists
        channels = collection.find({"channelName": {"$exists": True, "$ne": None}})

        channel_docs = []
        for channel in channels:
            channel_docs.append(
                {
                    "_id": channel["_id"],
                    "channelName": (
                        channel["channelName"].strip() if channel["channelName"] else ""
                    ),
                }
            )

        logger.info(f"Found {len(channel_docs)} documents with channelName")
        return channel_docs

    except Exception as e:
        logger.error(f"Error fetching channels from MongoDB: {e}")
        return []


def get_channel_ids_for_names(channel_names: List[str]) -> List[Dict[str, str]]:
    """
    Takes a list of channel names and returns a list of dictionaries
    with channelId and channelName mapping

    Args:
        channel_names: List of channel names to fetch IDs for

    Returns:
        List of dicts in format [{"channelId": "id", "channelName": "name"}]
    """
    youtube = Youtube()
    results = []

    for channel_name in channel_names:
        if not channel_name or not channel_name.strip():
            continue

        channel_id = get_channel_id_from_api(youtube, channel_name.strip())

        if channel_id:
            results.append(
                {"channelId": channel_id, "channelName": channel_name.strip()}
            )
            logger.info(f"Successfully mapped: {channel_name} -> {channel_id}")
        else:
            logger.warning(f"Could not find channel ID for: {channel_name}")

    return results


def get_channel_id_from_api(youtube: Youtube, channelName: str) -> Optional[str]:
    """Get channel ID for a given channel name using YouTube API"""
    try:
        response = youtube.execute(
            lambda svc: svc.search().list(
                q=channelName, part="snippet", type="channel", maxResults=1
            )
        )

        if response and "items" in response and response["items"]:
            # Per YouTube Data API, channel id is under id.channelId for search results
            channel_id = response["items"][0].get("id", {}).get("channelId")
            if channel_id:
                logger.info(f"Found channel ID for '{channelName}': {channel_id}")
                return channel_id

        else:
            logger.warning(f"Channel ID not found in response for '{channelName}'")
            return None
    except Exception as e:
        logger.error(f"Error getting channel ID for {channelName}: {e}")
        return None


def update_documents_with_channel_ids(channel_mappings: List[Dict[str, str]]) -> int:
    """
    Update MongoDB documents with channelId based on channelName

    Args:
        channel_mappings: List of dicts with channelId and channelName

    Returns:
        Number of documents updated
    """
    updated_count = 0

    try:
        for mapping in channel_mappings:
            channel_name = mapping["channelName"]
            channel_id = mapping["channelId"]

            # Update all documents with this channelName
            result = collection.update_many(
                {"channelName": channel_name},
                {"$set": {"channelId": channel_id}},
                upsert=True,
            )

            if result.modified_count > 0:
                updated_count += result.modified_count
                logger.info(
                    f"Updated {result.modified_count} documents for channel '{channel_name}' with ID: {channel_id}"
                )
            else:
                logger.warning(f"No documents updated for channel: {channel_name}")

        logger.info(f"Total documents updated: {updated_count}")
        return updated_count

    except Exception as e:
        logger.error(f"Error updating documents with channel IDs: {e}")
        return updated_count


def main():
    """
    Main function to orchestrate the entire process:
    1. Fetch channels from MongoDB
    2. Get channel IDs for channel names
    3. Update documents with channel IDs
    """
    logger.info("Starting channel ID mapping process...")

    # Step 1: Fetch channels from MongoDB
    channel_docs = fetch_channels_from_mongo()
    if not channel_docs:
        logger.error("No channels found in MongoDB. Exiting.")
        return

    # Extract unique channel names
    unique_channel_names = list(
        set([doc["channelName"] for doc in channel_docs if doc["channelName"]])
    )
    logger.info(f"Found {len(unique_channel_names)} unique channel names")

    # Step 2: Get channel IDs for these names
    channel_mappings = get_channel_ids_for_names(unique_channel_names)
    if not channel_mappings:
        logger.error("No channel IDs found. Exiting.")
        return

    logger.info(f"Successfully retrieved {len(channel_mappings)} channel ID mappings")

    # Step 3: Update documents with channel IDs
    updated_count = update_documents_with_channel_ids(channel_mappings)

    logger.info(
        f"Process completed. Updated {updated_count} documents with channel IDs."
    )

    # Print summary
    print(f"\n=== SUMMARY ===")
    print(f"Total unique channels processed: {len(unique_channel_names)}")
    print(f"Channel IDs found: {len(channel_mappings)}")
    print(f"Documents updated: {updated_count}")

    return channel_mappings


# Legacy function for backward compatibility
def get_channel_id(channelName: str) -> Optional[str]:
    """Legacy function - use get_channel_id_from_api instead"""
    youtube = Youtube()
    return get_channel_id_from_api(youtube, channelName)


if __name__ == "__main__":
    main()
