import requests
import json
import os
import re
from pymongo import MongoClient
import pytz
from datetime import datetime, timedelta
import sys


HEADERS = {
    "Authorization": "Bearer AAAAAAAAAAAAAAAAAAAAAJPhvAEAAAAApoR8d4G4bI%2FHSoUh5Jwci%2BffvV8%3DqjFGW8HlNxlbFUd6sPTmJUcT3wgC9iiarirLElEj1DeWrG2so9"
}


def fetch_json(url):
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 429:
        print("Rate limit exceeded. Stopping the script.")
        sys.exit(1)  # Exit the script with a status code of 1
    else:
        print(f"Failed to fetch the data: {response.status_code}")
        return None


def sanitize_filename(query):
    sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1F]', "_", query)
    sanitized = sanitized[:200]
    return sanitized


def build_query(query_params):
    query_string = query_params.get("query", "")
    query_string += "-is:retweet"
    # (from:mhadaofficial OR MHADA OR Mhada Lottary OR %MhadaLottary OR Mhada Lottary OR म्हाडा OR म्हाडाची OR Maharashtra Housing and Area Development Authority OR BDD Chawl OR Dangerous Cessed Buildings OR (MHADA AND (Legal Dispute OR Environmental Concerns OR Policy Changes OR Public Feedback OR Infrastructure Initiatives OR Redevelopment Projects OR Housing Scheme Updates OR Lottery Results OR Millworkers)))
    # query_string = '(from:mhadaofficial OR MHADA OR Mhada Lottary OR (Mhada Lottary OR म्हाडा OR म्हाडाची) OR (BDD Chawl) OR (Dangerous Cessed Buildings) OR (Legal Dispute) OR (Millworkers) OR (ottery Results OR Millworkers))'
    # query_string="Mhada Housing"
    tweet_fields = query_params.get("tweet.fields", "")

    start_time = query_params.get("start_time", "")
    end_time = query_params.get("end_time", "")

    # url_params = f"query={query_string}&tweet.fields={tweet_fields}"

    # Get the current time and calculate the start time for 3 days ago
    now = datetime.utcnow()
    three_days_ago = now - timedelta(days=1)
    end_time = now - timedelta(seconds=60)
    # Format the start_time and end_time in ISO 8601 format
    start_time = three_days_ago.isoformat("T") + "Z"
    end_time = end_time.isoformat("T") + "Z"

    # Construct the URL parameters string
    url_params = f"query={query_string}&tweet.fields={tweet_fields}&start_time={start_time}&end_time={end_time}"

    return url_params


def fetch_tweets(query_params, max_results, next_token=None):
    url_params = build_query(query_params)
    print(url_params)
    # return None
    url = f"https://api.twitter.com/2/tweets/search/recent?{url_params}&max_results={max_results}&expansions=attachments.media_keys&media.fields=url"
    if next_token:
        url += f"&next_token={next_token}"
    return fetch_json(url)


def save_next_token(query, next_token):
    sanitized_query = sanitize_filename(query)
    with open(f"{sanitized_query}_next_token.json", "w") as file:
        json.dump({"next_token": next_token}, file)


def load_next_token(query):
    sanitized_query = sanitize_filename(query)
    if os.path.exists(f"{sanitized_query}_next_token.json"):
        with open(f"{sanitized_query}_next_token.json", "r") as file:
            return json.load(file).get("next_token")
    return None


def get_user_details(user_ids):
    url = f"https://api.twitter.com/2/users?ids={','.join(user_ids)}&user.fields=public_metrics,username,profile_image_url,location"
    user_data = fetch_json(url)
    if user_data:
        return {
            user["id"]: {
                "public_metrics": user["public_metrics"],
                "username": user["username"],
                "profile_image_url": user.get("profile_image_url", ""),
                "location": user.get("location", ""),
            }
            for user in user_data.get("data", [])
        }
    return {}


def fetch_and_save_tweets(query_params, max_results, next_token=None):
    try:
        tweets_data = fetch_tweets(query_params, max_results, next_token)
        if tweets_data:
            tweets = tweets_data.get("data", [])
            author_ids = list(set(tweet["author_id"] for tweet in tweets))

            user_details = get_user_details(author_ids)
            media = {
                media["media_key"]: media.get("url", "")
                for media in tweets_data.get("includes", {}).get("media", [])
            }

            filtered_tweets = []
            for tweet in tweets:
                author_id = tweet["author_id"]
                details = user_details.get(author_id, {})
                followers_count = details.get("public_metrics", {})
                username = details.get("username", "Unknown")
                profile_image_url = details.get("profile_image_url", "")
                location = details.get("location", "Unknown")

                tweet["_id"] = tweet["id"]  # Use tweet ID as MongoDB _id
                tweet["link"] = f"https://twitter.com/twitter/statuses/{tweet['id']}"
                tweet["author_name"] = username
                tweet["keywords"] = query_params["query"]
                tweet["profile_img"] = profile_image_url
                tweet["location"] = location
                tweet["followers_info"] = followers_count
                created_at = tweet.get("created_at", "")
                tz = pytz.UTC

                tweet["created_at"] = (
                    datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%S.%fZ").replace(
                        tzinfo=tz
                    )
                    if created_at
                    else ""
                )

                if "attachments" in tweet and "media_keys" in tweet["attachments"]:
                    tweet["media_urls"] = [
                        media.get(media_key, "")
                        for media_key in tweet["attachments"]["media_keys"]
                    ]
                else:
                    tweet["media_urls"] = []

                # Add key tag with client and company details in an array of objects
                tweet["tags"] = [
                    {
                        "clientId": query_params["clientId"],
                        "clientName": query_params["clientName"],
                        "companyId": query_params["companyId"],
                        "companyName": query_params["companyName"],
                    }
                ]

                filtered_tweets.append(tweet)

            result = {
                "tweets": filtered_tweets,
                "next_token": tweets_data.get("meta", {}).get("next_token", None),
            }

            save_tweets_to_mongodb(query_params["query"], result["tweets"])
            next_token = tweets_data.get("meta", {}).get("next_token", None)
            if next_token:
                save_next_token(query_params["query"], next_token)
            else:
                sanitized_query = sanitize_filename(query_params["query"])
                if os.path.exists(f"{sanitized_query}_next_token.json"):
                    os.remove(f"{sanitized_query}_next_token.json")
        else:
            raise Exception("No tweets data returned.")

    except Exception as e:
        print(f"An error occurred: {e}")
        # Stop further processing
        return


def save_tweets_to_mongodb(query, tweets):
    mongo_client = MongoClient(
        "mongodb://admin:Cir%5EPnq%406A@51.195.235.59:27017/smFeeds?authSource=admin"
    )
    mongo_db = mongo_client["smFeeds"]
    mongo_collection = mongo_db["xtweets"]

    for tweet in tweets:
        try:
            # Find  tweet
            existing_tweet = mongo_collection.find_one({"_id": tweet["_id"]})

            if existing_tweet:
                # Checking any changes in followrs
                followers_info_changed = (
                    existing_tweet.get("followers_info", {}) != tweet["followers_info"]
                )

                # Checking tags
                tag_exists = any(
                    tag["clientId"] == tweet["tags"][0]["clientId"]
                    and tag["companyId"] == tweet["tags"][0]["companyId"]
                    and tag["companyName"] == tweet["tags"][0]["companyName"]
                    and tag["clientName"] == tweet["tags"][0]["clientName"]
                    for tag in existing_tweet["tags"]
                )

                update_fields = {}

                # Update followers_info if it has changed
                if followers_info_changed:
                    update_fields["$set"] = {"followers_info": tweet["followers_info"]}

                # Add the new tag not present
                if not tag_exists:
                    if "$push" not in update_fields:
                        update_fields["$push"] = {}
                    update_fields["$push"]["tags"] = tweet["tags"][0]

                if update_fields:
                    mongo_collection.update_one({"_id": tweet["_id"]}, update_fields)
                    print(f"Updated tweet with ID: {tweet['_id']}")
                else:
                    print(f"No updates needed for tweet with ID: {tweet['_id']}")
            else:
                # Insert new twiiet
                mongo_collection.insert_one(tweet)
                print(f"Inserted tweet with ID: {tweet['_id']}")

        except Exception as e:
            print(f"Failed to insert or update tweet with ID {tweet['_id']}: {e}")


def get_queries_from_mongodb():
    mongo_client = MongoClient(
        "mongodb://admin:Cir%5EPnq%406A@51.195.235.59:27017/smFeeds?authSource=admin"
    )
    mongo_db = mongo_client["smFeeds"]
    search_keyword_collection = mongo_db["searchKeywords"]

    queries = search_keyword_collection.find({"type": "xfeed", "isActive": True})

    return [
        {
            "query": q["query"],
            "companyId": q["companyId"],
            "clientId": q["clientId"],
            "clientName": q["clientName"],
            "companyName": q["CompanyName"],
            "tweet.fields": "author_id,created_at,text,public_metrics",
        }
        for q in queries
    ]


if __name__ == "__main__":
    queries = get_queries_from_mongodb()
    max_results = 100

    for query in queries:
        print(query)

        fetch_and_save_tweets(query, max_results)
        while True:
            next_token = load_next_token(query["query"])
            if next_token:
                fetch_and_save_tweets(query, max_results, next_token)
            else:
                print(f"No more tweets to fetch for {query['query']}.")
                break
