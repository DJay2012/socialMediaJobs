"""
Twitter Scraper
Improved Twitter scraper using the new configuration system
"""

import requests
import json
import os
import re
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import pytz
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from baseSocialMediaScraper import BaseSocialMediaScraper
from socialMediaConfig import config


class TwitterScraper(BaseSocialMediaScraper):
    """Twitter scraper with improved error handling and security"""

    def __init__(self):
        super().__init__("Twitter")
        self.headers = {"Authorization": config.api.twitter_bearer_token}

    def sanitize_filename(self, query: str) -> str:
        """Sanitize filename for token storage"""
        sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1F]', "_", query)
        return sanitized[:200]

    def build_query(self, query_params: Dict) -> str:
        """Build search query with time parameters"""
        query_string = query_params.get("query", "")
        query_string += " -is:retweet"

        # Calculate time range (last 24 hours)
        now = datetime.utcnow()
        one_day_ago = now - timedelta(days=1)

        # Format dates for Twitter API
        start_time = one_day_ago.isoformat("T") + "Z"
        end_time = now.isoformat("T") + "Z"

        return f"{query_string} start_time:{start_time} end_time:{end_time}"

    def fetch_tweets(
        self, query_params: Dict, max_results: int, next_token: Optional[str] = None
    ) -> Optional[Dict]:
        """Fetch tweets from Twitter API with error handling"""
        try:
            query = self.build_query(query_params)
            url = "https://api.twitter.com/2/tweets/search/recent"

            params = {
                "query": query,
                "max_results": max_results,
                "tweet.fields": "author_id,created_at,text,public_metrics,attachments",
                "expansions": "attachments.media_keys",
                "media.fields": "url",
            }

            if next_token:
                params["next_token"] = next_token

            response = requests.get(url, headers=self.headers, params=params)

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                self.logger.error("Twitter API rate limit exceeded")
                return None
            elif response.status_code == 401:
                self.logger.error("Twitter API authentication failed")
                return None
            else:
                self.logger.error(
                    f"Twitter API error: {response.status_code} - {response.text}"
                )
                return None

        except Exception as e:
            self.logger.error(f"Error fetching tweets: {e}")
            return None

    def get_user_details(self, user_ids: List[str]) -> Dict[str, Dict]:
        """Fetch user details for given user IDs"""
        try:
            url = "https://api.twitter.com/2/users"
            params = {
                "ids": ",".join(user_ids),
                "user.fields": "public_metrics,username,profile_image_url,location",
            }

            response = requests.get(url, headers=self.headers, params=params)

            if response.status_code == 200:
                data = response.json()
                return {
                    user["id"]: {
                        "public_metrics": user["public_metrics"],
                        "username": user["username"],
                        "profile_image_url": user.get("profile_image_url", ""),
                        "location": user.get("location", ""),
                    }
                    for user in data.get("data", [])
                }
            else:
                self.logger.error(
                    f"Failed to fetch user details: {response.status_code}"
                )
                return {}

        except Exception as e:
            self.logger.error(f"Error fetching user details: {e}")
            return {}

    def save_next_token(self, query: str, next_token: str):
        """Save pagination token to file"""
        try:
            sanitized_query = self.sanitize_filename(query)
            token_file = f"tokens/{sanitized_query}_next_token.json"
            os.makedirs(os.path.dirname(token_file), exist_ok=True)

            with open(token_file, "w") as file:
                json.dump({"next_token": next_token}, file)
        except Exception as e:
            self.logger.error(f"Error saving next token: {e}")

    def load_next_token(self, query: str) -> Optional[str]:
        """Load pagination token from file"""
        try:
            sanitized_query = self.sanitize_filename(query)
            token_file = f"tokens/{sanitized_query}_next_token.json"

            if os.path.exists(token_file):
                with open(token_file, "r") as file:
                    return json.load(file).get("next_token")
            return None
        except Exception as e:
            self.logger.error(f"Error loading next token: {e}")
            return None

    def processSingleKeyword(self, keyword_data: Dict[str, str]) -> bool:
        """Process a single search keyword"""
        try:
            query = keyword_data["query"]
            self.logger.info(f"Processing Twitter query: {query}")

            collection = self.getCollection(config.database.collections["xtweets"])

            # Process all pages of results
            while True:
                next_token = self.load_next_token(query)
                tweets_data = self.retryWithBackoff(
                    self.fetch_tweets, keyword_data, config.app.max_results, next_token
                )

                if not tweets_data:
                    self.logger.warning(f"No tweets data returned for query: {query}")
                    break

                tweets = tweets_data.get("data", [])
                if not tweets:
                    self.logger.info(f"No tweets found for query: {query}")
                    break

                # Process tweets
                success_count = self._process_tweets(
                    tweets, tweets_data, keyword_data, collection
                )
                self.logger.info(f"Processed {success_count} tweets for query: {query}")

                # Check for next page
                next_token = tweets_data.get("meta", {}).get("next_token")
                if next_token:
                    self.save_next_token(query, next_token)
                else:
                    # Clean up token file if no more pages
                    sanitized_query = self.sanitize_filename(query)
                    token_file = f"tokens/{sanitized_query}_next_token.json"
                    if os.path.exists(token_file):
                        os.remove(token_file)
                    break

                # Rate limiting
                self.rateLimitDelay()

            return True

        except Exception as e:
            self.logger.error(
                f"Error processing keyword {keyword_data.get('query', 'unknown')}: {e}"
            )
            return False

    def _process_tweets(
        self, tweets: List[Dict], tweets_data: Dict, keyword_data: Dict, collection
    ) -> int:
        """Process and save tweet data"""
        success_count = 0

        # Get user details
        author_ids = list(set(tweet["author_id"] for tweet in tweets))
        user_details = self.get_user_details(author_ids)

        # Get media information
        media = {
            media["media_key"]: media.get("url", "")
            for media in tweets_data.get("includes", {}).get("media", [])
        }

        for tweet in tweets:
            try:
                author_id = tweet["author_id"]
                user_info = user_details.get(author_id, {})

                # Prepare tweet data
                tweet_data = {
                    "_id": tweet["id"],
                    "id": tweet["id"],
                    "text": tweet["text"],
                    "created_at": self.parsePublishedAt(tweet["created_at"]),
                    "author_id": author_id,
                    "author_name": user_info.get("username", "Unknown"),
                    "link": f"https://twitter.com/twitter/statuses/{tweet['id']}",
                    "profile_img": user_info.get("profile_image_url", ""),
                    "location": user_info.get("location", "Unknown"),
                    "keywords": keyword_data["query"],
                    "followers_info": user_info.get("public_metrics", {}),
                    "public_metrics": tweet.get("public_metrics", {}),
                    "media_urls": self._extract_media_urls(tweet, media),
                }

                # Add client tags
                tweet_data = self.addClientTags(tweet_data, keyword_data)

                # Save to database
                if self.checkAndUpdateExistingRecord(
                    collection, tweet["id"], tweet_data
                ):
                    success_count += 1

            except Exception as e:
                self.logger.error(
                    f"Error processing tweet {tweet.get('id', 'unknown')}: {e}"
                )
                continue

        return success_count

    def _extract_media_urls(self, tweet: Dict, media: Dict) -> List[str]:
        """Extract media URLs from tweet"""
        media_urls = []
        if "attachments" in tweet and "media_keys" in tweet["attachments"]:
            for media_key in tweet["attachments"]["media_keys"]:
                if media_key in media:
                    media_urls.append(media[media_key])
        return media_urls


def main():
    """Main function to run the Twitter scraper"""
    scraper = TwitterScraper()
    scraper.run("xfeed")


if __name__ == "__main__":
    main()
