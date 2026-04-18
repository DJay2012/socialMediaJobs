"""
Data Migration Class for Social Media Platforms
Handles data migration between different MongoDB collections for various social media platforms
"""

from dataclasses import dataclass
from pymongo import MongoClient
from datetime import datetime, timedelta
from pymongo.collection import Collection
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional, Dict, Any, Union, Unpack
from src.database.operation import get_sequence_id, get_social_feed_id
from src.schema.SocialFeed import SocialFeedSchema
from src.config.config import config
from src.types.enums import SocialFeedType
from src.types.types import DataMigrationConfigType
from src.log.logging import logger
from src.utils.helper import (
    format_date,
    get_today_end,
    get_today_start,
    normalize_to_datetime,
)


@dataclass
class DataMigrationConfig:
    """Configuration settings for DataMigration class with flexible setters"""

    source_uri: str = config.database.uri
    target_uri: str = config.database.uri_production
    source_db: str = "smFeeds"
    target_db: str = "pnq"
    sharded_collections: List[str] = None
    batch_size: int = 1000
    thread_count: int = 4
    retry_attempts: int = 3
    retry_delay: float = 1.0  # seconds

    def __post_init__(self):
        """Initialize default values after dataclass creation"""
        if self.sharded_collections is None:
            self.sharded_collections = ["socialFeed", "article"]


class DataMigration:
    """
    Data migration class for handling different social media platform data
    """

    def __init__(self, platform: str):
        # Initialize configuration
        self._config = DataMigrationConfig()

        # Initialize database connections
        self.source_client = None
        self.target_client = None
        self.source_collection: Collection = None
        self.target_collection: Collection = None

        # Initialize platform and schema
        self.start_date = get_today_start()
        self.end_date = get_today_end()
        self.platform = platform
        self.schema: Union[SocialFeedSchema, None] = None
        self.social_feed_type = {}

    def _set_schema(self, schema: SocialFeedSchema):
        """Set the schema for the data migration"""
        self.schema = schema
        self._get_social_feed_type()

    def _get_social_feed_type(self):
        """Get the social feed type for the data migration"""
        with MongoClient(self._config.target_uri) as client:
            db = client[self._config.target_db]
            collection = db["socialFeedType"]
            platform = self.platform.lower()

            self.social_feed_type = (
                collection.find_one({"active": True, "name": platform}) or {}
            )

            return self.social_feed_type

    def _connect_database(self, source: str, target: str):
        """Connect to source and destination MongoDB instances using settings"""
        try:
            # Validate parameters
            if not source or not target:
                raise ValueError("Source and target collection names are required")

            self.source_client = MongoClient(self._config.source_uri)
            self.target_client = MongoClient(self._config.target_uri)

            # Test database connections
            source_db = self.source_client[self._config.source_db]
            target_db = self.target_client[self._config.target_db]
            self.source_collection = source_db[source]
            self.target_collection = target_db[target]

            logger.success(f"Connected to source and destination databases")
        except Exception as e:
            logger.error(f"Failed to connect to databases: {e}")
            raise

    def _disconnect_database(self):
        """Close database connections"""
        if self.source_client:
            self.source_client.close()
        if self.target_client:
            self.target_client.close()
        logger.success("Database connections closed")

    def _process_document(self, document: Dict[str, Any]):
        """
        Process a single document based on data type
        """
        try:
            # Validate document has required _id
            if "_id" not in document:
                logger.error("Document missing required '_id' field")
                return None

            platform = self.platform

            # Apply data type specific processing
            if platform == SocialFeedType.YOUTUBE:
                document = self._process_youtube(document)

            elif platform == SocialFeedType.TWITTER:
                document = self._process_twitter(document)

            elif platform == SocialFeedType.FACEBOOK:
                document = self._process_facebook(document)

            # Upsert the document
            if self.target_collection.name in self._config.sharded_collections:

                is_exists = self.target_collection.count_documents(
                    {"_id": document["_id"]}
                )

                if is_exists:
                    return self.target_collection.replace_one(
                        {"_id": document["_id"]}, document
                    )

                return self.target_collection.insert_one(document)

            self.target_collection.update_one(
                {"_id": document["_id"]}, {"$set": document}, upsert=True
            )

        except Exception as e:
            logger.error(
                f"Error processing document {document.get('_id', 'unknown')}: {str(e)}"
            )
            raise

    def _process_youtube(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process YouTube specific document transformations
        """
        # Add YouTube specific processing here
        if self.schema is not None:
            document = self.schema.from_youtube(
                document, self.social_feed_type
            ).to_dict()
            return document

        if "socialFeedId" not in document or document.get("socialFeedId") is None:
            document["socialFeedId"] = get_social_feed_id(
                self.platform, document["_id"]
            )
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

    def _migrate(self):
        """
        Migrate data between collections by date range with multithreading
        """
        try:
            # Use settings for max_workers if not provided
            max_workers = self._config.thread_count

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

                logger.note(
                    f"{self.platform} data migration completed. "
                    f"Processed: {completed_count}, Errors: {error_count}"
                )

        except Exception as e:
            logger.error(f"Fatal error during {self.platform} migration: {e}")
            raise

    def set_config(self, **kwargs: Unpack[DataMigrationConfigType]):
        """Set the configuration for the data migration"""
        try:
            # Update the internal config object
            for key, value in kwargs.items():
                if hasattr(self._config, key):
                    # Validate value type if possible
                    if hasattr(self._config, "__dataclass_fields__"):
                        field_info = self._config.__dataclass_fields__.get(key)
                        if field_info and hasattr(field_info, "type"):
                            # Basic type validation
                            expected_type = field_info.type
                            if not isinstance(value, expected_type):
                                logger.warning(
                                    f"Type mismatch for {key}: expected {expected_type}, got {type(value)}"
                                )

                    setattr(self._config, key, value)
                    setattr(self, key, value)  # Also set on instance
                else:
                    logger.warning(f"Unknown configuration key: {key}")

        except Exception as e:
            logger.error(f"Error setting configuration: {e}")
            raise

    def get_config(self) -> DataMigrationConfig:
        """Get the current configuration"""
        return self._config

    def migrate(
        self,
        source: str = None,
        target: str = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        validation_schema: Optional[SocialFeedSchema] = None,
    ):
        """
        Migrate YouTube data from source to destination
        """

        try:

            self._connect_database(source, target)

            if start_date and end_date:
                self.start_date = start_date
                self.end_date = end_date

            logger.info(
                f"Starting {self.platform} data migration: {source} -> {target}"
            )

            if validation_schema:
                self._set_schema(validation_schema)

            self._migrate()

        except Exception as e:
            logger.error(f"Fatal error during {self.platform} migration: {str(e)}")
            raise
        finally:
            self._disconnect_database()
