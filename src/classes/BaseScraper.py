"""
Base class for social media scrapers
Provides common functionality for all social media data collection scripts
"""

import time
import math
from abc import ABC, abstractmethod
from typing import Dict, List, Any
from datetime import datetime
from dateutil import parser
from pymongo.collection import Collection
from pymongo import ReplaceOne
from pymongo.errors import BulkWriteError
import pytz
from pymongo.errors import DuplicateKeyError
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from config.config import config
from enums.types import KeywordEntity
from log.logging import logger
from utils.helper import request_delay


# Base class for all social media scrapers
class BaseScraper(ABC):

    def __init__(self, platform_name: str):
        self.platform_name = platform_name
        self.logger = logger
        self.mongo_client = None
        self.db = None
        self.db_lock = Lock()  # Thread safety for database operations
        self.keywords_per_thread = 10  # Number of keywords per thread

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

    # Get a specific collection (thread-safe)
    def get_collection(self, collectionName: str) -> Collection:
        with self.db_lock:
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

    def bulk_insert_or_replace(
        self, collection, data_list: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """
        Insert or replace records in MongoDB collection.
        If _id exists, replace the document; otherwise insert new document.

        Args:
            collection: MongoDB collection object
            data_list: List of documents to insert/replace

        Returns:
            Dictionary with counts of inserted, replaced, and failed operations
        """
        if not data_list:
            return {"inserted": 0, "replaced": 0, "failed": 0}

        results = {"inserted": 0, "replaced": 0, "failed": 0}

        try:
            operations = []
            for data in data_list:
                record_id = data.get("_id")
                if not record_id:
                    self.logger.warning(f"Skipping document without _id: {data}")
                    results["failed"] += 1
                    continue

                # Add bulk replace operation with upsert
                operations.append(ReplaceOne({"_id": record_id}, data, upsert=True))

            if not operations:
                return results

            # Execute bulk operation
            bulk_result = collection.bulk_write(operations, ordered=False)

            # Extract results
            results["inserted"] = bulk_result.upserted_count
            results["replaced"] = bulk_result.modified_count
            results["failed"] = len(data_list) - (
                results["inserted"] + results["replaced"]
            )

        except BulkWriteError as bwe:
            self.logger.error(f"Bulk write error: {bwe.details}")
            results["failed"] = len(data_list)

        except Exception as e:
            self.logger.error(f"Error in bulk insert/replace operation: {e}")
            results["failed"] = len(data_list)

        self.logger.note(
            f"Bulk operation completed - Inserted: {results['inserted']}, "
            f"Replaced: {results['replaced']}, Failed: {results['failed']}"
        )

        return results

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
        type: str,
        search_by: Dict[str, Any] = None,
        limit: int = None,
    ) -> List[Dict[str, str]]:

        collection = self.get_collection(config.database.collections["search_keywords"])

        query = {"type": type, "isActive": True}
        if search_by:
            query.update(search_by)

        collection_data = collection.find(query)
        if limit is not None:
            collection_data = collection_data.limit(limit)

        return list(collection_data)

    def _calculate_max_workers(self, total_keywords: int) -> int:
        """Calculate optimal number of threads based on keywords count"""
        if total_keywords <= 0:
            return 1

        max_workers = math.ceil(total_keywords / self.keywords_per_thread)
        # Limit to reasonable number of threads (max 50 to avoid overwhelming the system)
        return min(max_workers, 50)

    def _chunk_keywords(
        self, keywords: List[Dict[str, Any]], chunk_size: int
    ) -> List[List[Dict[str, Any]]]:
        """Split keywords into chunks for thread processing"""
        chunks = []
        for i in range(0, len(keywords), chunk_size):
            chunks.append(keywords[i : i + chunk_size])
        return chunks

    def process_keyword_chunk(
        self, keyword_chunk: List[Dict[str, Any]], thread_id: int
    ) -> Dict[str, int]:
        """Process a chunk of keywords in a single thread"""
        results = {"processed": 0, "successful": 0, "failed": 0}

        self.logger.info(
            f"Thread {thread_id}: Processing {len(keyword_chunk)} keywords"
        )

        for index, keyword in enumerate(keyword_chunk):
            try:
                key = None

                for key_enum in KeywordEntity:
                    if (
                        key_enum.value in keyword
                        and keyword[key_enum.value] is not None
                    ):
                        key = key_enum.value
                        break

                value = keyword.get(key, None)

                self.logger.info(
                    f"Thread {thread_id}: Processing {key}: {value} - {index + 1} of {len(keyword_chunk)}"
                )

                success = self.process_keyword(keyword)
                results["processed"] += 1

                if success:
                    results["successful"] += 1
                    self.logger.success(
                        f"Thread {thread_id}: Successfully processed {key}: {value}"
                    )
                else:
                    results["failed"] += 1
                    self.logger.warning(
                        f"Thread {thread_id}: Failed to process {key}: {value}"
                    )

                # Rate limiting delay
                request_delay()

            except Exception as e:
                results["processed"] += 1
                results["failed"] += 1
                self.logger.error(
                    f"Thread {thread_id}: Error processing keyword {index + 1}: {e}"
                )
                continue

        self.logger.info(
            f"Thread {thread_id} completed: {results['successful']}/{results['processed']} successful"
        )
        return results

    @abstractmethod
    def process_keyword(self, data: Dict[str, Any]) -> bool:
        # Process a single search keyword - must be implemented by subclasses
        pass

    # Main run method for the scraper (with threading support)
    def run(
        self,
        type,
        search_by: Dict[str, Any] = None,
        limit: int = None,
        use_threading: bool = True,
    ):
        start_time = time.time()

        try:
            self.connect_db()
            search_keywords = self.get_search_keywords(type, search_by, limit)
            total_keywords = len(search_keywords)

            self.logger.note(
                f"Loaded {total_keywords} search queries for {self.platform_name}"
            )

            if not search_keywords:
                self.logger.warning("No keywords to process")
                return

            if use_threading and total_keywords > 1:
                self._run_threaded(search_keywords, total_keywords)
            else:
                self._run_sequential(search_keywords, total_keywords)

            elapsed_time = time.time() - start_time
            self.logger.note(
                f"Completed processing for {self.platform_name} - {total_keywords} search queries in {elapsed_time:.2f} seconds"
            )

        except Exception as e:
            self.logger.error(f"Fatal error in {self.platform_name} scraper: {e}")
            raise
        finally:
            self.disconnect_db()

    def _run_threaded(self, search_keywords: List[Dict[str, Any]], total_keywords: int):
        """Run keyword processing using ThreadPoolExecutor"""

        # Calculate optimal number of threads
        max_workers = self._calculate_max_workers(total_keywords)

        # Split keywords into chunks
        keyword_chunks = self._chunk_keywords(search_keywords, self.keywords_per_thread)

        # Enable threaded logging format to show thread names in console
        self.logger.enable_threaded_format()

        self.logger.note(
            f"Starting threaded processing: {max_workers} threads, {len(keyword_chunks)} chunks, "
            f"{self.keywords_per_thread} keywords per thread"
        )

        total_results = {"processed": 0, "successful": 0, "failed": 0}

        with ThreadPoolExecutor(
            max_workers=max_workers, thread_name_prefix=f"{self.platform_name}_worker"
        ) as executor:
            # Submit all chunks to the thread pool
            future_to_thread = {}
            for thread_id, chunk in enumerate(keyword_chunks, 1):
                future = executor.submit(self.process_keyword_chunk, chunk, thread_id)
                future_to_thread[future] = thread_id

            # Collect results as they complete
            for future in as_completed(future_to_thread):
                thread_id = future_to_thread[future]
                try:
                    results = future.result()
                    total_results["processed"] += results["processed"]
                    total_results["successful"] += results["successful"]
                    total_results["failed"] += results["failed"]

                    self.logger.info(f"Thread {thread_id} completed successfully")

                except Exception as e:
                    self.logger.error(f"Thread {thread_id} failed with error: {e}")
                    continue

        self.logger.note(
            f"Threading completed - Total: {total_results['processed']}, "
            f"Successful: {total_results['successful']}, Failed: {total_results['failed']}"
        )

        # Disable threaded logging format after completion
        self.logger.disable_threaded_format()

    def _run_sequential(
        self, search_keywords: List[Dict[str, Any]], total_keywords: int
    ):
        """Run keyword processing sequentially (fallback method)"""

        self.logger.info("Running in sequential mode")

        for index, keyword in enumerate(search_keywords):
            try:
                key = None

                for key_enum in KeywordEntity:
                    if (
                        key_enum.value in keyword
                        and keyword[key_enum.value] is not None
                    ):
                        key = key_enum.value
                        break

                value = keyword.get(key, None)

                self.logger.info(
                    f"Processing {key}: {value} - {index + 1} of {total_keywords}"
                )
                success = self.process_keyword(keyword)

                if success:
                    self.logger.success(
                        f"Successfully processed {key}: {value} - {index + 1} of {total_keywords}"
                    )
                else:
                    self.logger.warning(
                        f"Failed to process {key}: {value} - {index + 1} of {total_keywords}"
                    )

                # Rate limiting delay
                request_delay()

            except Exception as e:
                self.logger.error(
                    f"Error processing {key}: {value} - {index + 1} of {total_keywords}: {e}"
                )
                continue
