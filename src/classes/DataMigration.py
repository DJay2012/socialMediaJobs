"""
Data Migration Class for Social Media Platforms
Handles data migration between different MongoDB collections for various social media platforms
"""

from pymongo import MongoClient
from datetime import datetime, timedelta
from pymongo.collection import Collection
from pymongo.database import Database
import pytz
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Dict, Any
from config.config import config
from enums.types import Platform
from log.logging import logger
from utils.helper import format_date, normalize_to_datetime


class DataMigration:
    """
    Data migration class for handling different social media platform data
    """

    def __init__(self, platform: Platform):
        """
        Initialize DataMigration with a platform.
        """
        self.source_client = None
        self.destination_client = None
        self.source_db: Database = None
        self.destination_db: Database = None
        self.source_collection: Collection = None
        self.destination_collection: Collection = None
        self.start_date = None
        self.end_date = None
        self.platform: Platform = platform.value
        self.end_date = None

    def _connect_database(self, source, destination):
        """Connect to source and destination MongoDB instances"""
        try:
            self.source_client = MongoClient(config.database.uri)
            self.destination_client = MongoClient(config.database.uri_production)

            self.source_db = self.source_client["smFeeds"]
            self.destination_db = self.destination_client["pnq"]
            self.source_collection = self.source_db[source]
            self.destination_collection = self.destination_db[destination]

            logger.success("Connected to source and destination databases")
        except Exception as e:
            logger.error(f"Failed to connect to databases: {e}")
            raise

    def _disconnect_database(self):
        """Close database connections"""
        if self.source_client:
            self.source_client.close()
        if self.destination_client:
            self.destination_client.close()
        logger.success("Database connections closed")

    def _process_document(self, document: Dict[str, Any]):
        """
        Process a single document based on data type
        """
        try:
            # ist = pytz.timezone("Asia/Kolkata")
            platform = self.platform

            # Convert publishedAt to IST if present
            # if "publishedAt" in document:
            #     document["publishedAt"] = document["publishedAt"].astimezone(ist)

            # Apply data type specific processing
            if platform == Platform.YOUTUBE:
                document = self._process_youtube(document)
            elif platform == Platform.TWITTER:
                document = self._process_twitter(document)
            elif platform == Platform.FACEBOOK:
                document = self._process_facebook(document)

            # Upsert the document
            self.destination_collection.replace_one(
                {"_id": document["_id"]}, document, upsert=True
            )

        except Exception as e:
            logger.error(
                f"Error processing document {document.get('_id', 'unknown')}: {e}"
            )
            raise

    def _process_youtube(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process YouTube specific document transformations
        """
        # Add YouTube specific processing here
        # For now, just ensure required fields are present
        # if "platform" not in document:
        #     document["platform"] = "youtube"

        # Ensure statistics field exists
        # if "statistics" not in document:
        #     document["statistics"] = {}

        # Normalize channel information
        if "channel" not in document:
            document["channel"] = {
                "id": document.get("channelId", None),
                "title": document.get("channelTitle", None),
            }

        return document

    def _process_twitter(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process Twitter specific document transformations
        TODO: Implement Twitter specific processing
        """
        if "platform" not in document:
            document["platform"] = "twitter"

        logger.warning("Twitter document processing not yet implemented")
        return document

    def _process_facebook(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process Facebook specific document transformations
        TODO: Implement Facebook specific processing
        """
        if "platform" not in document:
            document["platform"] = "facebook"

        logger.warning("Facebook document processing not yet implemented")
        return document

    def _migrate(self, max_workers: int = 5):
        """
        Migrate data between collections by date range with multithreading
        """
        try:
            current_date = normalize_to_datetime(self.start_date)
            end_date = normalize_to_datetime(self.end_date)
            formatted_start_date = format_date(current_date)
            formatted_end_date = format_date(end_date)

            logger.info(
                f"Starting {self.platform} data migration"
                + (f" from {formatted_start_date}" if self.start_date else None)
                + (f" to {formatted_end_date}" if self.end_date else None)
            )

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = []

                while current_date <= end_date:
                    next_date = current_date + timedelta(days=1)

                    documents = self.source_collection.find(
                        {"publishedAt": {"$gte": current_date, "$lt": next_date}}
                    )

                    for document in documents:
                        futures.append(
                            executor.submit(self._process_document, document)
                        )

                    logger.info(
                        f"Submitted tasks for date: {current_date.strftime('%Y-%m-%d')} ({self.platform})"
                    )
                    current_date = next_date

                # Wait for all tasks to complete
                completed_count = 0
                error_count = 0

                for future in as_completed(futures):
                    try:
                        future.result()
                        completed_count += 1
                    except Exception as e:
                        error_count += 1
                        logger.error(f"Error processing document: {e}")

                logger.success(
                    f"{self.platform} data migration completed. "
                    f"Processed: {completed_count}, Errors: {error_count}"
                )

        except Exception as e:
            logger.error(f"Fatal error during {self.platform} migration: {e}")
            raise

    def migrate(
        self,
        source: str,
        destination: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ):
        """
        Migrate YouTube data from source to destination
        """

        try:

            self._connect_database(source, destination)
            self.start_date = start_date
            self.end_date = end_date

            logger.info(
                f"Starting {self.platform} data migration: {source} -> {destination}"
            )

            self._migrate()

        except Exception as e:
            logger.error(f"Fatal error during {self.platform} migration: {str(e)}")
            raise
        finally:
            self._disconnect_database()
