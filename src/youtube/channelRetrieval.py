"""
Channel Retrieval
Specialized scraper for YouTube channel data collection
"""

from typing import Any, Dict

from src.classes.DataMigration import DataMigration
from src.types.enums import SocialFeedType
from src.classes.BaseScraper import BaseScraper
from src.classes.Youtube import Youtube
from src.schema.Youtube import ChannelSchema
from src.config.config import config

production_uri = config.database.uri_production
collections = config.database.collections


# Channel Retrieval for specific channel data collection
class ChannelRetrieval(BaseScraper):

    # Initialize Channel Retrieval
    def __init__(self):
        super().__init__("Channel Retrieval")
        self.youtube = Youtube()

    def _process_channel_data(self, channel_ids: Dict[str, Any], **extras):
        """Process Channel data and return structured format"""
        processed_data = []
        channel_details = self.youtube.get_channel_info(channel_ids, format="dict")

        for _id, channel in channel_details.items():
            try:
                if _id not in channel_details:
                    self.logger.warning(f"Channel details not found for {_id}")
                    continue

                processed_data.append(ChannelSchema.from_api(channel).to_dict())
            except Exception as e:
                self.logger.error(f"Error processing channel {_id}: {str(e)}")
                continue

        return processed_data

    # Search for influencer content in a specific channel
    def _search(self, data):

        try:

            query = data.get("query", "")

            search_results = self.youtube.search_query(query, pagination=False)

            channel_ids = [
                result["snippet"]["channelId"] for result in search_results.values()
            ]

            if not channel_ids:
                self.logger.warning(f"No channels found for {query}")
                return True

            collection = self.get_collection(collections["youtube_channels"])

            processed_data = self._process_channel_data(channel_ids)
            self.bulk_insert_or_replace(collection, processed_data)

            return True

        except Exception as e:
            self.logger.error(f"Error in ChannelRetrieval._search: {e}")
            return False

    # Process a single search keyword for BMW channels
    def process_keyword(self, data: Dict[str, Any]) -> bool:

        try:
            return self._search(data)

        except Exception as e:
            self.logger.error(f"Error processing Channel Retrieval: {e}")
            return False


# Main function to run the Channel Retrieval
def channel_retrieval(keyword: str, start_date: str = None, end_date: str = None):
    scraper = ChannelRetrieval()
    if start_date and end_date:
        scraper.youtube.set_date_range(start_date, end_date)

    scraper.run(keyword)

    # migration = DataMigration(keyword)
    # migration.migrate(
    #     source="youtube",
    #     destination="youtube",
    #     start_date=start_date,
    #     end_date=end_date,
    # )


if __name__ == "__main__":
    channel_retrieval(
        SocialFeedType.YOUTUBE_CHANNEL_RETRIEVAL.value,
        "2025-09-01T00:00:00Z",
        "2025-09-26T23:59:59Z",
    )
