"""
Base class for social media scrapers
Provides common functionality for all social media data collection scripts
"""

import time
import random
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime
import pytz
from pymongo.errors import DuplicateKeyError
from config.config import config
from log.logging import logger


# Base class for all social media scrapers
class BaseScraper(ABC):

    def __init__(self, platform_name: str):
        self.platform_name = platform_name
        self.logger = logger
        self.mongo_client = None
        self.db = None

    # Connect to MongoDB database
    def connectToDatabase(self):
        try:
            self.mongo_client = config.getMongoClient()
            self.db = self.mongo_client[config.database.db_name]
            self.logger.success(f"Connected to MongoDB for {self.platform_name}")
        except Exception as e:
            self.logger.error(f"Failed to connect to database: {e}")
            raise

    # Close MongoDB connection
    def closeDatabaseConnection(self):
        if self.mongo_client:
            self.mongo_client.close()
            self.logger.success("Database connection closed")

    # Get a specific collection
    def getCollection(self, collectionName: str):
        if self.db is None:
            self.connectToDatabase()
        return self.db[collectionName]

    # Parse published date string to UTC datetime
    def parsePublishedAt(self, publishedAt: str) -> datetime:
        tz = pytz.UTC
        try:
            return datetime.strptime(publishedAt, "%Y-%m-%dT%H:%M:%S.%fZ").replace(
                tzinfo=tz
            )
        except ValueError:
            return datetime.strptime(publishedAt, "%Y-%m-%dT%H:%M:%SZ").replace(
                tzinfo=tz
            )

    # Add client and company tags to data
    def addClientTags(
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

    def checkAndUpdateExistingRecord(
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
    def retryWithBackoff(self, func, *args, **kwargs):
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

        # Add random delay to respect rate limits

    def rateLimitDelay(self):
        delay = random.uniform(
            config.app.rate_limit_delay, config.app.rate_limit_delay * 2
        )
        time.sleep(delay)

    # Get search keywords from database
    def getSearchKeywords(
        self, searchType: str, clientFilter: Optional[str] = None
    ) -> List[Dict[str, str]]:
        collection = self.getCollection(config.database.collections["search_keywords"])

        query = {"type": searchType}
        if clientFilter:
            query["clientid"] = clientFilter

        keywords = []
        for doc in collection.find(query):
            keyword_data = {
                "query": doc.get("query", ""),
                "clientId": doc.get("clientid", ""),
                "clientName": doc.get("clientName", ""),
                "companyId": doc.get("companyid", ""),
                "companyName": doc.get("CompanyName", ""),
            }

            # Add additional fields for specific job types
            if "channel_name" in doc:
                keyword_data["channel_name"] = doc.get("channel_name", "")
            if "influencer_name" in doc:
                keyword_data["influencer_name"] = doc.get("influencer_name", "")

            keywords.append(keyword_data)

        return keywords

    @abstractmethod
    def processSingleKeyword(self, keywordData: Dict[str, str]) -> bool:
        # Process a single search keyword - must be implemented by subclasses
        pass

    # Main run method for the scraper
    def run(self, searchType: str, clientFilter: Optional[str] = None):
        try:
            self.connectToDatabase()
            keywords = self.getSearchKeywords(searchType, clientFilter)

            self.logger.info(
                f"Processing {len(keywords)} keywords for {self.platform_name}"
            )

            for keywordData in keywords:
                try:
                    self.logger.info(f"Processing keyword: {keywordData['query']}")
                    success = self.processSingleKeyword(keywordData)

                    if success:
                        self.logger.info(
                            f"Successfully processed: {keywordData['query']}"
                        )
                    else:
                        self.logger.warning(
                            f"Failed to process: {keywordData['query']}"
                        )

                    # Rate limiting delay
                    self.rateLimitDelay()

                except Exception as e:
                    self.logger.error(
                        f"Error processing keyword {keywordData['query']}: {e}"
                    )
                    continue

            self.logger.info(f"Completed processing for {self.platform_name}")

        except Exception as e:
            self.logger.error(f"Fatal error in {self.platform_name} scraper: {e}")
            raise
        finally:
            self.closeDatabaseConnection()
