import requests
import json
from pymongo import MongoClient
from datetime import datetime, timedelta
import time
import pytz

BEARER_TOKEN = 'Bearer AAAAAAAAAAAAAAAAAAAAAJPhvAEAAAAApoR8d4G4bI%2FHSoUh5Jwci%2BffvV8%3DqjFGW8HlNxlbFUd6sPTmJUcT3wgC9iiarirLElEj1DeWrG2so9'

MONGO_CONNECTION_STRING = 'mongodb://admin:Cir%5EPnq%406A@51.195.235.59:27017/'

USERNAMES = ['LalitKModi', 'ruchirlmodi', 'DrBkModi1']

BASE_URL = 'https://api.twitter.com/2/'

headers = {
    "Authorization": BEARER_TOKEN
}

client = MongoClient(MONGO_CONNECTION_STRING)
db = client['smFeeds']
collection = db['xtweets']

tz = pytz.UTC

def get_user_id(username):
    url = f'{BASE_URL}users/by/username/{username}'
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        user_data = response.json()
        return user_data['data']['id'], user_data['data']
    else:
        print(f"Error fetching user ID for {username}: {response.status_code}")
        return None, None

def get_latest_tweets(user_id, tweet_count=10, start_date=None, end_date=None):
    url = f'{BASE_URL}users/{user_id}/tweets'
    params = {
        'max_results': tweet_count,
        'tweet.fields': 'author_id,created_at,text,public_metrics,attachments',
    }
    
   
    if start_date:
        params['start_time'] = start_date.strftime('%Y-%m-%dT%H:%M:%SZ')
    if end_date:
        params['end_time'] = end_date.strftime('%Y-%m-%dT%H:%M:%SZ')
    
    all_tweets = []
    while True:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            all_tweets.extend(data.get('data', []))
            
            next_token = data.get('meta', {}).get('next_token')
            if next_token:
                params['pagination_token'] = next_token
            else:
                break
        else:
            print(f"Error fetching tweets for user {user_id}: {response.status_code}")
            break
    return all_tweets

def save_tweet_to_mongo(tweet, username, user_id, user_info):
    tags = []
    if username == "LalitKModi":
        tags = [
            {
                "clientId": "GODFREY",
                "clientName": "GODFREY PHILLIPS INDIA LIMITED",
                "companyId": "LA_MOD",
                "companyName": "LALIT MODI"
            }
        ]
    elif username == "ruchirlmodi":
        tags = [
            {
                "clientId": "GODFREY",
                "clientName": "GODFREY PHILLIPS INDIA LIMITED",
                "companyId": "GODFREY",
                "companyName": "RUCHIR MODI"
            }
        ]
    elif username == "DrBkModi1":
        tags = [
            {
                "clientId": "GODFREY",
                "clientName": "GODFREY PHILLIPS INDIA LIMITED",
                "companyId": "BK_MODI",
                "companyName": "DR BK MODI"
            }
        ]
    
    tweet_data = {
        "_id": tweet['id'],
        "text": tweet['text'],
        "public_metrics": tweet['public_metrics'],
        "created_at": datetime.strptime(tweet['created_at'], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=tz) if tweet['created_at'] else '',

        "author_id": user_id,
        "author_name": username,
        "link": f"https://twitter.com/{username}/status/{tweet['id']}",
        "followers_info": {
            "followers_count": user_info.get('public_metrics', {}).get('followers_count', 0),
            "following_count": user_info.get('public_metrics', {}).get('following_count', 0),
            "tweet_count": user_info.get('public_metrics', {}).get('tweet_count', 0),
            "listed_count": user_info.get('public_metrics', {}).get('listed_count', 0),
            "like_count": user_info.get('public_metrics', {}).get('like_count', 0)
        },
        "media_urls": tweet.get('attachments', {}).get('media_keys', []),
        "profile_img": user_info.get('profile_image_url', 'https://abs.twimg.com/sticky/default_profile_images/default_profile_normal.png'),
        "location": user_info.get('location', ''),
        "createdAt": datetime.utcnow(),
        "tags": tags  
    }
    
    try:
        if collection.find_one({"_id": tweet['id']}):
            print(f"Tweet ID {tweet['id']} already exists. Skipping insertion.")
        else:
            collection.insert_one(tweet_data)
            print(f"Tweet ID {tweet['id']} saved to MongoDB.")
    except Exception as e:
        print(f"Error saving tweet to MongoDB: {e}")

if __name__ == '__main__':
    processed_usernames = set()
    
    
    start_date = datetime.utcnow() - timedelta(days=6)  
    end_date = datetime.utcnow()  
    
    while True:
        for username in USERNAMES:
            if username not in processed_usernames:
                user_id, user_info = get_user_id(username)
                if user_id:
                    print(f"Fetching tweets for {username} (ID: {user_id})")
                    tweets = get_latest_tweets(user_id, start_date=start_date, end_date=end_date)
                    if tweets:
                        for tweet in tweets:
                            save_tweet_to_mongo(tweet, username, user_id, user_info)
                    else:
                        print(f"No tweets found for {username}")
                    
                    processed_usernames.add(username)  
                    print(f"Processed {username}")
                
                print('-' * 80)
                
                time.sleep(1500)  # Sleep for 25 minutes before fetching again
        
        if len(processed_usernames) == len(USERNAMES):
            processed_usernames.clear()  
            print("All usernames processed. Restarting the cycle...")
        
        print("Waiting 15 seconds before repeating the process...")
        time.sleep(1500)  # Sleep for 25 minutes before starting a new cycle
        
        
