"""
Data Migration Class for Social Media Platforms
Handles data migration between different MongoDB collections for various social media platforms
"""

from pymongo import MongoClient
from datetime import datetime, timedelta
import pytz
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Dict, Any
from config.config import config
from types.types import Platform
from log.logging import logger


class DataMigration:
    """
    Data migration class for handling different social media platform data
    """

    def __init__(self):
        self.logger = logger
        self.source_client = None
        self.destination_client = None
        self.source_db = None
        self.destination_db = None

    def connect_database(self):
        """Connect to source and destination MongoDB instances"""
        try:
            self.source_client = MongoClient(config.database.uri)
            self.destination_client = MongoClient(config.database.uri_production)

            self.source_db = self.source_client["smFeeds"]
            self.destination_db = self.destination_client["pnq"]

            self.logger.success("Connected to source and destination databases")
        except Exception as e:
            self.logger.error(f"Failed to connect to databases: {e}")
            raise

    def disconnect_database(self):
        """Close database connections"""
        if self.source_client:
            self.source_client.close()
        if self.destination_client:
            self.destination_client.close()
        self.logger.success("Database connections closed")

    def process_document(
        self, document: Dict[str, Any], destination_collection, data_type: Platform
    ):
        """
        Process a single document based on data type
        """
        try:
            ist = pytz.timezone("Asia/Kolkata")

            # Convert publishedAt to IST if present
            if "publishedAt" in document:
                document["publishedAt"] = document["publishedAt"].astimezone(ist)

            # Apply data type specific processing
            if data_type == Platform.YOUTUBE:
                document = self._process_youtube_document(document)
            elif data_type == Platform.TWITTER:
                document = self._process_twitter_document(document)
            elif data_type == Platform.FACEBOOK:
                document = self._process_facebook_document(document)

            # Upsert the document
            destination_collection.replace_one(
                {"_id": document["_id"]}, document, upsert=True
            )

        except Exception as e:
            self.logger.error(
                f"Error processing document {document.get('_id', 'unknown')}: {e}"
            )
            raise

    def _process_youtube_document(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process YouTube specific document transformations
        """
        # Add YouTube specific processing here
        # For now, just ensure required fields are present
        if "platform" not in document:
            document["platform"] = "youtube"

        # Ensure statistics field exists
        if "statistics" not in document:
            document["statistics"] = {}

        # Normalize channel information
        if "channelTitle" in document and "channel" not in document:
            document["channel"] = {
                "title": document["channelTitle"],
                "id": document.get("channelId", ""),
            }

        return document

    def _process_twitter_document(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process Twitter specific document transformations
        TODO: Implement Twitter specific processing
        """
        if "platform" not in document:
            document["platform"] = "twitter"

        self.logger.warning("Twitter document processing not yet implemented")
        return document

    def _process_facebook_document(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process Facebook specific document transformations
        TODO: Implement Facebook specific processing
        """
        if "platform" not in document:
            document["platform"] = "facebook"

        self.logger.warning("Facebook document processing not yet implemented")
        return document

    def migrate_data_by_date(
        self,
        data_type: Platform,
        source_collection_name: str,
        destination_collection_name: str,
        start_date: datetime,
        end_date: datetime,
        max_workers: int = 5,
    ):
        """
        Migrate data between collections by date range with multithreading
        """
        try:
            if not self.source_db or not self.destination_db:
                self.connect_database()

            source_collection = self.source_db[source_collection_name]
            destination_collection = self.destination_db[destination_collection_name]

            current_date = start_date

            self.logger.info(
                f"Starting {data_type.value} data migration from {start_date} to {end_date}"
            )

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = []

                while current_date <= end_date:
                    next_date = current_date + timedelta(days=1)

                    documents = source_collection.find(
                        {"createdAt": {"$gte": current_date, "$lt": next_date}}
                    )

                    for document in documents:
                        futures.append(
                            executor.submit(
                                self.process_document,
                                document,
                                destination_collection,
                                data_type,
                            )
                        )

                    self.logger.info(
                        f"Submitted tasks for date: {current_date.strftime('%Y-%m-%d')} ({data_type.value})"
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
                        self.logger.error(f"Error processing document: {e}")

                self.logger.success(
                    f"{data_type.value} data migration completed. "
                    f"Processed: {completed_count}, Errors: {error_count}"
                )

        except Exception as e:
            self.logger.error(f"Fatal error during {data_type.value} migration: {e}")
            raise

    def migrate_youtube_data(
        self,
        source_collection: str = "bmw",
        destination_collection: str = "youtube",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ):
        """
        Migrate YouTube data from source to destination
        """
        if not start_date:
            start_date = datetime.now(pytz.utc)
        if not end_date:
            end_date = datetime.now(pytz.utc) - timedelta(days=2)

        self.logger.info(
            f"Starting YouTube data migration: {source_collection} -> {destination_collection}"
        )

        self.migrate_data_by_date(
            data_type=Platform.YOUTUBE,
            source_collection_name=source_collection,
            destination_collection_name=destination_collection,
            start_date=start_date,
            end_date=end_date,
        )

    def migrate_twitter_data(
        self,
        source_collection: str = "twitter",
        destination_collection: str = "twitter",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ):
        """
        Migrate Twitter data from source to destination
        TODO: Implement Twitter specific migration logic
        """
        self.logger.warning("Twitter data migration not yet implemented")
        # Placeholder for future implementation
        pass

    def migrate_facebook_data(
        self,
        source_collection: str = "facebook",
        destination_collection: str = "facebook",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ):
        """
        Migrate Facebook data from source to destination
        TODO: Implement Facebook specific migration logic
        """
        self.logger.warning("Facebook data migration not yet implemented")
        # Placeholder for future implementation
        pass


def main():
    """Main function for backward compatibility"""
    migration = DataMigration()

    try:
        migration.connect_database()

        # Default YouTube migration (maintaining original behavior)
        end_date = datetime.now(pytz.utc) - timedelta(days=2)
        start_date = datetime.now(pytz.utc)

        migration.migrate_youtube_data(
            source_collection="bmw",
            destination_collection="youtube",
            start_date=start_date,
            end_date=end_date,
        )

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise
    finally:
        migration.disconnect_database()


if __name__ == "__main__":
    main()
