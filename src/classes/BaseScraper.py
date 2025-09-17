"""
Base class for social media scrapers
Provides common functionality for all social media data collection scripts
"""

import time
import random
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime
from dateutil import parser
import pytz
from pymongo.errors import DuplicateKeyError
from config.config import config
from config.CredentialManager import credential_manager
from log.logging import logger
from utils.helper import request_delay


# Base class for all social media scrapers
class BaseScraper(ABC):

    def __init__(self, platform_name: str):
        self.platform_name = platform_name
        self.logger = logger
        self.mongo_client = None
        self.db = None

    # Connect to MongoDB database
    def connect_db(self):
        try:
            self.mongo_client = config.getMongoClient()
            self.db = self.mongo_client[config.database.db_name]
            self.logger.success(f"Connected to MongoDB for {self.platform_name}")
        except Exception as e:
            self.logger.error(f"Failed to connect to database: {e}")
            raise

    # Close MongoDB connection
    def disconnect_db(self):
        if self.mongo_client:
            self.mongo_client.close()
            self.logger.success("Database connection closed")

    # Get a specific collection
    def get_collection(self, collectionName: str):
        if self.db is None:
            self.connect_db()
        return self.db[collectionName]

    # Parse published date string to UTC datetime
    def parse_published_at(self, publishedAt: str) -> datetime:
        tz = pytz.UTC
        dt = parser.isoparse(publishedAt)

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=tz)
        else:
            dt = dt.astimezone(tz)
        return dt

    # Add client and company tags to data
    def add_client_tags(
        self, data: Dict[str, Any], clientInfo: Dict[str, str]
    ) -> Dict[str, Any]:
        data["tags"] = [
            {
                "clientId": clientInfo.get("clientId", ""),
                "clientName": clientInfo.get("clientName", ""),
                "companyId": clientInfo.get("companyId", ""),
                "companyName": clientInfo.get("companyName", ""),
            }
        ]
        return data

    def check_and_update_existing_record(
        self, collection, recordId: str, newData: Dict[str, Any]
    ) -> bool:
        """Check if record exists and update if needed"""
        try:
            existingRecord = collection.find_one({"_id": recordId})

            if existingRecord:
                # Check if tags need updating
                tagExists = any(
                    tag.get("clientId") == newData["tags"][0]["clientId"]
                    and tag.get("companyId") == newData["tags"][0]["companyId"]
                    for tag in existingRecord.get("tags", [])
                )

                updateFields = {}

                # Check for changes in metrics/followers
                if "followers_info" in newData and "followers_info" in existingRecord:
                    if existingRecord["followers_info"] != newData["followers_info"]:
                        updateFields["$set"] = {
                            "followers_info": newData["followers_info"]
                        }

                if "statistics" in newData and "statistics" in existingRecord:
                    if existingRecord["statistics"] != newData["statistics"]:
                        if "$set" not in updateFields:
                            updateFields["$set"] = {}
                        updateFields["$set"]["statistics"] = newData["statistics"]

                # Add new tag if it doesn't exist
                if not tagExists:
                    if "$push" not in updateFields:
                        updateFields["$push"] = {}
                    updateFields["$push"]["tags"] = newData["tags"][0]

                if updateFields:
                    collection.update_one({"_id": recordId}, updateFields)
                    self.logger.info(f"Updated {self.platform_name} record: {recordId}")
                    return True
                else:
                    self.logger.debug(
                        f"No updates needed for {self.platform_name} record: {recordId}"
                    )
                    return False
            else:
                # Insert new record
                collection.insert_one(newData)
                self.logger.info(
                    f"Inserted new {self.platform_name} record: {recordId}"
                )
                return True

        except DuplicateKeyError:
            self.logger.warning(
                f"Duplicate key error for {self.platform_name} record: {recordId}"
            )
            return False
        except Exception as e:
            self.logger.error(
                f"Error processing {self.platform_name} record {recordId}: {e}"
            )
            return False

    # Retry a function with exponential backoff
    def retry_with_backoff(self, func, *args, **kwargs):
        for attempt in range(config.app.retry_attempts):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                self.logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt < config.app.retry_attempts - 1:
                    delay = config.app.retry_delay * (2**attempt)
                    self.logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                else:
                    self.logger.error(f"All retry attempts failed for {func.__name__}")
                    raise

    # Get search keywords from database
    def get_search_keywords(
        self,
        search_type: str,
        filter: Optional[str] = None,
        additional_fields: Optional[dict[str, Any]] = None,
    ) -> List[Dict[str, str]]:
        collection = self.get_collection(config.database.collections["search_keywords"])

        query = {"type": search_type}
        if filter:
            query.update(filter)

        keywords = []
        find_kwargs = additional_fields or {}
        collection_data = collection.find(query, **find_kwargs)

        for doc in collection_data:
            keyword_data = {
                "query": doc.get("query", self.platform_name),
                "clientId": doc.get("clientId", ""),
                "clientName": doc.get("clientName", ""),
                "companyId": doc.get("companyId", ""),
                "companyName": doc.get("CompanyName", ""),
                "keywords": doc.get("keywords", []),
            }

            # Add additional fields for specific job types
            if "channelName" in doc:
                keyword_data["channelName"] = doc.get("channelName", "")
            if "influencerName" in doc:
                keyword_data["influencerName"] = doc.get("influencerName", "")

            keywords.append(keyword_data)

        return keywords

    @abstractmethod
    def process_single_keyword(self, keyword_data: Dict[str, Any]) -> bool:
        # Process a single search keyword - must be implemented by subclasses
        pass

    # Main run method for the scraper
    def run(
        self,
        search_type: str,
        filter: Optional[str] = None,
        additional_fields: Optional[Dict[str, str]] = None,
    ):
        try:
            self.connect_db()
            keywords = self.get_search_keywords(search_type, filter, additional_fields)

            self.logger.info(
                f"Processing {len(keywords)} keywords for {self.platform_name}"
            )

            for keyword_data in keywords:
                try:
                    self.logger.info(f"Processing keyword: {keyword_data['query']}")
                    success = self.process_single_keyword(keyword_data)

                    if success:
                        self.logger.success(
                            f"Successfully processed: {keyword_data['query'] or keyword_data['channelName']}"
                        )
                    else:
                        self.logger.warning(
                            f"Failed to process: {keyword_data['query'] or keyword_data['channelName']}"
                        )

                    # Rate limiting delay
                    request_delay()

                except Exception as e:
                    self.logger.error(
                        f"Error processing keyword {keyword_data['query'] or keyword_data['channelName']}: {e}"
                    )
                    continue

            self.logger.info(f"Completed processing for {self.platform_name}")

        except Exception as e:
            self.logger.error(f"Fatal error in {self.platform_name} scraper: {e}")
            raise
        finally:
            self.disconnect_db()
