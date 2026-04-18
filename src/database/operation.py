from typing import Dict, List
from pymongo import MongoClient, UpdateOne
from src.config.config import config
from src.log.logging import logger
from src.utils.cache import Cache

MONGO_URI = config.database.uri_production


def get_sequence_id(counter_name):
    """Get the next sequence id for the given counter name"""
    if not counter_name:
        logger.error("Counter name is required")
        return None

    try:
        with MongoClient(MONGO_URI) as mongoClient:
            db = mongoClient["pnq"]

            result = db.sequence.find_one_and_update(
                {"_id": counter_name},
                {"$inc": {"sequenceValue": 1}},
                upsert=True,
                return_document=True,
            )

            if result and "sequenceValue" in result:
                return int(result["sequenceValue"])
            else:
                logger.error(f"Invalid sequence result for counter: {counter_name}")
                return None

    except Exception as e:
        logger.error(f"Error getting sequence id for counter '{counter_name}': {e}")
        return None


def get_social_feed_id(platform: str, _id: str):
    """Get the social feed id for the given _id"""

    if not platform or not _id:
        logger.error("Platform and _id are required")
        return None

    cache = Cache()
    cache_key = f"{platform}:{_id}"
    if cache.has(cache_key):
        return cache.get(cache_key)

    try:
        with MongoClient(MONGO_URI) as mongoClient:
            db = mongoClient["pnq"]
            collection = db[platform]
            doc = collection.find_one({"_id": _id})
            social_feed_id = None

            if doc is None:
                social_feed_id = get_sequence_id("socialFeedId")

            elif "socialFeedId" not in doc:
                social_feed_id = get_sequence_id("socialFeedId")

            else:
                social_feed_id = doc["socialFeedId"]

            cache.set(cache_key, social_feed_id)
            return social_feed_id
    except Exception as e:
        logger.error(
            f"Error getting social feed id for platform '{platform}', _id '{_id}': {e}"
        )
        return None


def insert_social_feed_tags(social_feed_tags: List[Dict]):
    """
    Insert or update social feed tags with proper validation and error handling
    """
    if not social_feed_tags:
        logger.warning("No social feed tags to process")
        return

    try:
        with MongoClient(MONGO_URI) as mongoClient:
            db = mongoClient["pnq"]
            collection = db.socialFeedTag

            social_feed_ids = [tag["socialFeedId"] for tag in social_feed_tags]
            total_inserted = 0
            total_updated = 0
            total_errors = 0

            # Process each tag using upsert for efficiency
            for tag in social_feed_tags:
                try:

                    is_exists = collection.find_one({"_id": tag["_id"]})
                    if is_exists:
                        result = collection.update_one(
                            {"_id": tag["_id"]}, {"$set": tag}
                        )
                    else:
                        result = collection.insert_one(tag)

                    # Check if it was an insert or update
                    if (
                        result
                        and hasattr(result, "modified_count")
                        and result.modified_count > 0
                    ):
                        total_updated += 1
                    elif (
                        result and hasattr(result, "inserted_id") and result.inserted_id
                    ):
                        total_inserted += 1
                    # If neither, document already exists with same data

                except Exception as e:
                    logger.error(
                        f"Error upserting social feed tag with _id={tag.get('_id')}: {e}"
                    )
                    total_errors += 1
                    continue

            # Log summary
            total_processed = total_inserted + total_updated
            if total_processed > 0:
                logger.success(
                    f"Processed {total_processed} social feed tags "
                    f"(inserted: {total_inserted}, updated: {total_updated}) "
                    f"for socialFeedIds: {social_feed_ids}"
                )
            else:
                logger.warning(
                    f"No changes made to social feed tags for socialFeedIds: {set(social_feed_ids)}"
                )

            if total_errors > 0:
                logger.error(f"Failed to process {total_errors} social feed tags")

    except Exception as e:
        logger.error(f"Error inserting social feed tags: {e}")
        return None


def update_social_feed_id_to_youtube(_id: str, social_feed_id: int):
    """Update the social feed id to youtube"""
    try:
        with MongoClient(MONGO_URI) as mongoClient:
            db = mongoClient["pnq"]
            collection = db.youtube
            collection.update_one(
                {"_id": _id}, {"$set": {"socialFeedId": social_feed_id}}
            )
    except Exception as e:
        logger.error(f"Error updating social feed id to youtube: {e}")
        return None
