import asyncio
from twscrape import API, gather
from twscrape.logger import set_log_level
import json
import os
import re
from pymongo import MongoClient
import pytz
from datetime import datetime, timedelta
import sys
from typing import List, Dict, Optional
import time

async def init_api():
    """Initialize the API with accounts"""
    api = API()
    
    # You need to add accounts first time you run the script
    # Uncomment and modify these lines for first time setup
    await api.add_account("@kumarpnq", "Cirrus@Pnq", "kumar@pnq.co.in", "Cirrus@Pnq")
    # await api.add_account("username2", "password2", "email2", "email_password2")
    
    await api.pool.login_all()
    return api

def sanitize_filename(query: str) -> str:
    sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '_', query)
    return sanitized[:200]

def build_query(query_params: Dict) -> str:
    """Build search query with parameters"""
    query_string = query_params.get('query', '')
    query_string += ' -filter:retweets'
    
    # Calculate time range (last 24 hours)
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=1)
    
    # Format dates for query
    date_query = f' since:{start_time.strftime("%Y-%m-%d")} until:{end_time.strftime("%Y-%m-%d")}'
    return query_string + date_query

async def fetch_tweets(api: API, query_params: Dict, max_results: int) -> List[Dict]:
    """Fetch tweets using twscrape"""
    query = build_query(query_params)
    tweets = []
    
    try:
        # Fetch tweets
        async for tweet in api.search(query, limit=max_results):
            # Extract media URLs
            media_urls = []
            if tweet.media:
                for media in tweet.media:
                    if hasattr(media, 'url'):
                        media_urls.append(media.url)
            
            # Create tweet object
            tweet_obj = {
                '_id': str(tweet.id),
                'id': str(tweet.id),
                'text': tweet.rawContent,
                'created_at': tweet.date.replace(tzinfo=pytz.UTC),
                'author_id': str(tweet.user.id),
                'author_name': tweet.user.username,
                'link': f"https://twitter.com/twitter/statuses/{tweet.id}",
                'profile_img': tweet.user.profileImageUrl,
                'location': tweet.user.location or "Unknown",
                'keywords': query_params['query'],
                'followers_info': {
                    'followers_count': tweet.user.followersCount,
                    'following_count': tweet.user.followingCount,
                    'tweet_count': tweet.user.statusesCount,
                },
                'media_urls': media_urls,
                'tags': [{
                    "clientId": query_params['clientId'],
                    "clientName": query_params['clientName'],
                    "companyId": query_params['companyId'],
                    "companyName": query_params['companyName']
                }],
                'public_metrics': {
                    'retweet_count': tweet.retweetCount,
                    'reply_count': tweet.replyCount,
                    'like_count': tweet.likeCount,
                    'quote_count': tweet.quoteCount
                }
            }
            tweets.append(tweet_obj)
            
            # Add small delay to avoid rate limiting
            await asyncio.sleep(0.1)
            
    except Exception as e:
        print(f"Error fetching tweets: {e}")
        return []
    
    return tweets

def save_tweets_to_mongodb(query: str, tweets: List[Dict]):
    """Save tweets to MongoDB with duplicate handling"""
    mongo_client = MongoClient('mongodb://admin:Cir%5EPnq%406A@51.195.235.59:27017/smFeeds?authSource=admin')
    mongo_db = mongo_client['smFeeds']
    mongo_collection = mongo_db['xtweets']
    
    for tweet in tweets:
        try:
            existing_tweet = mongo_collection.find_one({"_id": tweet["_id"]})
            
            if existing_tweet:
                followers_info_changed = existing_tweet.get("followers_info", {}) != tweet["followers_info"]
                
                tag_exists = any(
                    tag["clientId"] == tweet['tags'][0]["clientId"] and
                    tag["companyId"] == tweet['tags'][0]["companyId"]
                    for tag in existing_tweet["tags"]
                )
                
                update_fields = {}
                
                if followers_info_changed:
                    update_fields["$set"] = {"followers_info": tweet["followers_info"]}
                
                if not tag_exists:
                    if "$push" not in update_fields:
                        update_fields["$push"] = {}
                    update_fields["$push"]["tags"] = tweet['tags'][0]
                
                if update_fields:
                    mongo_collection.update_one({"_id": tweet["_id"]}, update_fields)
                    print(f"Updated tweet {tweet['_id']}")
            else:
                mongo_collection.insert_one(tweet)
                print(f"Inserted new tweet {tweet['_id']}")
                
        except Exception as e:
            print(f"Error saving tweet {tweet['_id']}: {e}")

def get_queries_from_mongodb() -> List[Dict]:
    """Fetch search queries from MongoDB"""
    mongo_client = MongoClient('mongodb://admin:Cir%5EPnq%406A@51.195.235.59:27017/smFeeds?authSource=admin')
    mongo_db = mongo_client['smFeeds']
    search_keyword_collection = mongo_db['searchKeywords']
    
    queries = search_keyword_collection.find({"type": "xfeed", "isActive": True})
    
    return [{
        "query": q["query"],
        "companyId": q["companyid"],
        "clientId": q["clientid"],
        "clientName": q["clientName"],
        "companyName": q["CompanyName"],
        "tweet.fields": "author_id,created_at,text,public_metrics"
    } for q in queries]

async def main():
    # Set log level to reduce output
    set_log_level("INFO")
    
    # Initialize API
    api = await init_api()
    
    queries = get_queries_from_mongodb()
    max_results = 100

    for query in queries:
        print(f"Processing query: {query['query']}")
        tweets = await fetch_tweets(api, query, max_results)
        print("tweets", tweets)
        if tweets:
            save_tweets_to_mongodb(query['query'], tweets)
        else:
            print(f"No tweets found for query: {query['query']}")
        
        # Add delay between queries
        await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(main())