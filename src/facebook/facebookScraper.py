"""
Facebook Scraper
Improved Facebook scraper using Apify API
Based on the original MainapifyFacebook.py but improved
"""

import requests
import time
import pytz
from datetime import datetime
from typing import Dict

from classes.BaseScraper import BaseScraper
from config.config import config


class FacebookScraper(BaseScraper):
    """Facebook scraper using Apify API"""

    def __init__(self):
        super().__init__("Facebook")
        self.apify_api_token = config.api.apify_api_token
        self.actor_id = config.api.apify_actor_id
        self.base_url = "https://api.apify.com/v2"
        self.username = "kumarpnq"  # Apify username

    def start_actor_and_get_run_id(self, query: str):
        """Start Apify actor and get run ID"""
        try:
            actor_input = {
                "max_posts": 5,
                "max_retries": 5,
                "proxy": {"useApifyProxy": False},
                "query": query,
                "recent_posts": True,
                "search_type": "posts",
            }

            response = requests.post(
                f"{self.base_url}/actor-tasks/{self.username}~{self.actor_id}/runs?token={self.apify_api_token}",
                json=actor_input,
            )

            if response.status_code == 201:
                run_id = response.json()["data"]["id"]
                return run_id
            else:
                self.logger.error(f"Error starting actor: {response.status_code}")
                self.logger.error(f"Response: {response.json()}")
                return None
        except Exception as e:
            self.logger.error(f"Error starting Apify actor: {e}")
            return None

    def is_run_finished(self, run_id: str):
        """Check if Apify actor run is finished"""
        try:
            response = requests.get(
                f"{self.base_url}/actor-runs/{run_id}?token={self.apify_api_token}"
            )

            if response.status_code == 200:
                status = response.json()["data"]["status"]
                return status in ["SUCCEEDED", "FAILED", "ABORTED"]
            else:
                self.logger.error(f"Error checking run status: {response.status_code}")
                return False
        except Exception as e:
            self.logger.error(f"Error checking run status: {e}")
            return False

    def get_run_data(self, run_id: str, query: str, client_info: dict):
        """Get data from completed Apify run"""
        try:
            response = requests.get(
                f"{self.base_url}/actor-runs/{run_id}/dataset/items?token={self.apify_api_token}&format=json"
            )

            if response.status_code != 200:
                self.logger.error(f"Error fetching run data: {response.status_code}")
                return False

            data = response.json()
            collection = self.getCollection(config.database.collections["facebook"])
            processed_count = 0

            for post in data:
                # Skip posts without message or with error message
                if (
                    "message" not in post
                    or post["message"] == "No results. Try with proxy"
                ):
                    continue

                # Prepare post data
                post_data = {
                    "_id": post.get("post_id", None),
                    "type": "post",
                    "url": post.get("url", None),
                    "message": post.get("message", None),
                    "timestamp": post.get("timestamp", None),
                    "create_date": post.get("create_date", None),
                    "comments_count": post.get("comments_count", None),
                    "reactions_count": post.get("reactions_count", None),
                    "author": post.get(
                        "author", {"id": None, "name": None, "url": None}
                    ),
                    "image": post.get("image", None),
                    "video": post.get("video", None),
                    "attached_post_url": post.get("attached_post_url", None),
                    "query": query,
                    "location": None,
                }

                # Convert create_date to datetime
                created_at = post.get("create_date", None)
                if created_at:
                    tz = pytz.UTC
                    post_data["createdAt"] = datetime.strptime(
                        created_at, "%Y-%m-%dT%H:%M:%S"
                    ).replace(tzinfo=tz)
                else:
                    post_data["createdAt"] = None

                # Add client tags
                post_data = self.addClientTags(post_data, client_info)

                # Check and update existing record
                if self.checkAndUpdateExistingRecord(
                    collection, post_data["_id"], post_data
                ):
                    processed_count += 1

            self.logger.info(f"Processed {processed_count} Facebook posts")
            return True

        except Exception as e:
            self.logger.error(f"Error getting run data: {e}")
            return False

    def processSingleKeyword(self, keyword_data: Dict[str, str]) -> bool:
        """Process a single search keyword"""
        try:
            query = keyword_data["query"]
            self.logger.info(f"Processing Facebook query: {query}")

            # Prepare client info
            client_info = {
                "clientId": keyword_data.get("clientId", ""),
                "clientName": keyword_data.get("clientName", ""),
                "companyId": keyword_data.get("companyId", ""),
                "companyName": keyword_data.get("companyName", ""),
            }

            # Start Apify actor
            run_id = self.start_actor_and_get_run_id(query)
            if not run_id:
                return False

            self.logger.info(f"Apify actor started with run ID: {run_id}")

            # Wait for completion
            while not self.is_run_finished(run_id):
                self.logger.info("Waiting for Apify actor to complete...")
                time.sleep(60)  # Wait 1 minute before checking again

            # Get results
            success = self.get_run_data(run_id, query, client_info)

            if success:
                self.logger.info(f"Successfully processed Facebook query: {query}")
            else:
                self.logger.error(f"Failed to process Facebook query: {query}")

            return success

        except Exception as e:
            self.logger.error(f"Error processing Facebook keyword: {e}")
            return False


def main():
    """Main function to run the Facebook scraper"""
    scraper = FacebookScraper()
    scraper.run("facebook")


if __name__ == "__main__":
    main()
