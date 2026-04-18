"""
Modi Twitter Scraper
Specialized scraper for Modi family Twitter accounts
Based on the original ModiXfeed.py but improved
"""

import requests
from datetime import datetime, timedelta
from typing import Dict

from classes.BaseScraper import BaseScraper
from config.config import config


class ModiTwitterScraper(BaseScraper):
    """Modi family Twitter scraper"""

    def __init__(self):
        super().__init__("Modi Twitter")
        self.bearer_token = config.api.twitter_bearer_token
        self.base_url = "https://api.twitter.com/2/"
        self.headers = {"Authorization": self.bearer_token}

        # Modi family usernames
        self.usernames = ["LalitKModi", "ruchirlmodi", "DrBkModi1"]

    def get_user_id(self, username: str):
        """Get user ID for a given username"""
        try:
            url = f"{self.base_url}users/by/username/{username}"
            response = requests.get(url, headers=self.headers)

            if response.status_code == 200:
                user_data = response.json()
                return user_data["data"]["id"], user_data["data"]
            else:
                self.logger.error(
                    f"Error fetching user ID for {username}: {response.status_code}"
                )
                return None, None
        except Exception as e:
            self.logger.error(f"Error getting user ID for {username}: {e}")
            return None, None

    def get_latest_tweets(
        self, user_id: str, tweet_count: int = 10, start_date=None, end_date=None
    ):
        """Get latest tweets for a user"""
        try:
            url = f"{self.base_url}users/{user_id}/tweets"
            params = {
                "max_results": tweet_count,
                "tweet.fields": "author_id,created_at,text,public_metrics,attachments",
            }

            if start_date:
                params["start_time"] = start_date.strftime("%Y-%m-%dT%H:%M:%SZ")
            if end_date:
                params["end_time"] = end_date.strftime("%Y-%m-%dT%H:%M:%SZ")

            all_tweets = []
            while True:
                response = requests.get(url, headers=self.headers, params=params)

                if response.status_code == 200:
                    data = response.json()
                    all_tweets.extend(data.get("data", []))

                    next_token = data.get("meta", {}).get("next_token")
                    if next_token:
                        params["pagination_token"] = next_token
                    else:
                        break
                else:
                    self.logger.error(
                        f"Error fetching tweets for user {user_id}: {response.status_code}"
                    )
                    break

            return all_tweets
        except Exception as e:
            self.logger.error(f"Error getting tweets for user {user_id}: {e}")
            return []

    def get_modi_tags(self, username: str):
        """Get appropriate tags for Modi family members"""
        if username == "LalitKModi":
            return [
                {
                    "clientId": "GODFREY",
                    "clientName": "GODFREY PHILLIPS INDIA LIMITED",
                    "companyId": "LA_MOD",
                    "companyName": "LALIT MODI",
                }
            ]
        elif username == "ruchirlmodi":
            return [
                {
                    "clientId": "GODFREY",
                    "clientName": "GODFREY PHILLIPS INDIA LIMITED",
                    "companyId": "GODFREY",
                    "companyName": "RUCHIR MODI",
                }
            ]
        elif username == "DrBkModi1":
            return [
                {
                    "clientId": "GODFREY",
                    "clientName": "GODFREY PHILLIPS INDIA LIMITED",
                    "companyId": "BK_MODI",
                    "companyName": "DR BK MODI",
                }
            ]
        else:
            return []

    def process_single_keyword(self, keyword_data: Dict[str, str]) -> bool:
        """Process Modi family Twitter accounts"""
        try:
            collection = self.get_collection(config.database.collections["xtweets"])

            # Set date range (last 6 days)
            start_date = datetime.utcnow() - timedelta(days=6)
            end_date = datetime.utcnow()

            processed_count = 0

            for username in self.usernames:
                try:
                    self.logger.info(f"Processing Twitter account: {username}")

                    user_id, user_info = self.get_user_id(username)
                    if not user_id:
                        continue

                    tweets = self.get_latest_tweets(
                        user_id, start_date=start_date, end_date=end_date
                    )

                    if not tweets:
                        self.logger.info(f"No tweets found for {username}")
                        continue

                    # Process each tweet
                    for tweet in tweets:
                        try:
                            tweet_data = {
                                "_id": tweet["id"],
                                "text": tweet["text"],
                                "public_metrics": tweet["public_metrics"],
                                "created_at": self.parse_published_at(
                                    tweet["created_at"]
                                ),
                                "author_id": user_id,
                                "author_name": username,
                                "link": f"https://twitter.com/{username}/status/{tweet['id']}",
                                "followers_info": {
                                    "followers_count": user_info.get(
                                        "public_metrics", {}
                                    ).get("followers_count", 0),
                                    "following_count": user_info.get(
                                        "public_metrics", {}
                                    ).get("following_count", 0),
                                    "tweet_count": user_info.get(
                                        "public_metrics", {}
                                    ).get("tweet_count", 0),
                                    "listed_count": user_info.get(
                                        "public_metrics", {}
                                    ).get("listed_count", 0),
                                    "like_count": user_info.get(
                                        "public_metrics", {}
                                    ).get("like_count", 0),
                                },
                                "media_urls": tweet.get("attachments", {}).get(
                                    "media_keys", []
                                ),
                                "profile_img": user_info.get(
                                    "profile_image_url",
                                    "https://abs.twimg.com/sticky/default_profile_images/default_profile_normal.png",
                                ),
                                "location": user_info.get("location", ""),
                                "createdAt": datetime.utcnow(),
                                "tags": self.get_modi_tags(username),
                            }

                            # Check and update existing record
                            if self.check_and_update_existing_record(
                                collection, tweet["id"], tweet_data
                            ):
                                processed_count += 1

                        except Exception as e:
                            self.logger.error(
                                f"Error processing tweet {tweet.get('id', 'unknown')}: {e}"
                            )
                            continue

                    self.logger.info(f"Processed {len(tweets)} tweets for {username}")

                    # Rate limiting delay
                    self.rate_limit_delay()

                except Exception as e:
                    self.logger.error(f"Error processing account {username}: {e}")
                    continue

            self.logger.info(f"Total tweets processed: {processed_count}")
            return True

        except Exception as e:
            self.logger.error(f"Error in process_single_keyword: {e}")
            return False


def main():
    """Main function to run the Modi Twitter scraper"""
    scraper = ModiTwitterScraper()
    scraper.run("modi")


if __name__ == "__main__":
    main()
