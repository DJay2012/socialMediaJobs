from pymongo import MongoClient, errors
import requests
import time
import pytz
from datetime import datetime

# MongoDB connection
mongo_client = MongoClient('mongodb://admin:Cir%5EPnq%406A@51.195.235.59:27017/smFeeds?authSource=admin')
mongo_db = mongo_client['smFeeds']
search_keywords_collection = mongo_db['searchKeywords']
facebook_collection = mongo_db['facebook']

# Your Apify API token
APIFY_API_TOKEN = 'apify_api_ccTTQItkJTDrExWkioaSth36yK26Sx15bQsl'
# Your actor ID
ACTOR_ID = 'facebook-search-task'

# Base URL for Apify API
BASE_URL = 'https://api.apify.com/v2'

# Function to get search terms and related data from MongoDB
def get_search_terms():
    documents = search_keywords_collection.find({"type": "facebook"})
    search_terms_data = []
    for doc in documents:
        search_terms_data.append({
            "query": doc.get("query", ""),
            "clientId": doc.get("clientid", ""),
            "clientName": doc.get("clientName", ""),
            "companyId": doc.get("companyid", ""),
            "companyName": doc.get("CompanyName", "")
        })
    return search_terms_data

# Function to start the actor and get the run ID
def start_actor_and_get_run_id(query):
    ACTOR_INPUT = {
        "max_posts": 5,
        "max_retries": 5,
        "proxy": {
            "useApifyProxy": False
        },
        "query": query,  # Pass the query as a single string
        "recent_posts": True,
        "search_type": "posts"
    }
    
    # Your Apify username
    USER_NAME = 'kumarpnq'

    response = requests.post(
        f'{BASE_URL}/actor-tasks/{USER_NAME}~{ACTOR_ID}/runs?token={APIFY_API_TOKEN}',
        json=ACTOR_INPUT
    )

    if response.status_code == 201:
        run_id = response.json()['data']['id']
        return run_id
    else:
        print(f"Error: {response.status_code}")
        print(f"Response: {response.json()}")
        raise Exception('Failed to start actor')

# Function to check if the actor run is finished
def is_run_finished(run_id):
    response = requests.get(
        f'{BASE_URL}/actor-runs/{run_id}?token={APIFY_API_TOKEN}'
    )

    if response.status_code == 200:
        status = response.json()['data']['status']
        return status in ['SUCCEEDED', 'FAILED', 'ABORTED']
    else:
        print(f"Error: {response.status_code}")
        print(f"Response: {response.json()}")
        raise Exception('Failed to fetch run status')

# Function to get data from a specific run
def get_run_data(run_id, query, clientId, clientName, companyId, companyName):
    response = requests.get(
        f'{BASE_URL}/actor-runs/{run_id}/dataset/items?token={APIFY_API_TOKEN}&format=json'
    )
    if response.status_code == 200:
        data = response.json()

        for post in data:
            # Skip posts without a message or with "No results. Try with proxy" message
            if "message" not in post or post["message"] == "No results. Try with proxy":
                continue

            # Set missing fields to None (null in MongoDB)
            post['_id'] = post.get('post_id', None)
            post['type'] = 'post'
            post['url'] = post.get('url', None)
            post['message'] = post.get('message', None)
            post['timestamp'] = post.get('timestamp', None)
            post['create_date'] = post.get('create_date', None)
            post['comments_count'] = post.get('comments_count', None)
            post['reactions_count'] = post.get('reactions_count', None)
            post['author'] = post.get('author', {
                'id': None,
                'name': None,
                'url': None
            })
            post['image'] = post.get('image', None)
            post['video'] = post.get('video', None)
            post['attached_post_url'] = post.get('attached_post_url', None)
            post['tags'] = [
                {
                    "clientId": clientId,
                    "clientName": clientName,
                    "companyId": companyId,
                    "companyName": companyName
                }
            ]
            post['query'] = query
            post['location'] = None

            # Convert create_date to datetime and add it as createdAt
            created_at = post.get('create_date', None)
            if created_at:
                tz = pytz.UTC
                post['createdAt'] = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=tz)
            else:
                post['createdAt'] = None

            try:
                # Check if the post already exists in the collection
                existing_post = facebook_collection.find_one({"_id": post["_id"]})

                if existing_post:
                    # Check if the tag exists
                    tag_exists = any(
                        tag["clientId"] == clientId and
                        tag["companyId"] == companyId and
                        tag["companyName"] == companyName and
                        tag["clientName"] == clientName
                        for tag in existing_post.get("tags", [])
                    )

                    # If the tag doesn't exist, append it to the tags array
                    if not tag_exists:
                        facebook_collection.update_one(
                            {"_id": post["_id"]},
                            {"$push": {"tags": post['tags'][0]}}
                        )
                        print(f"Updated tags for post with ID: {post['_id']}")
                    else:
                        print(f"No updates needed for post with ID: {post['_id']}")
                else:
                    # Insert the post if it doesn't exist
                    facebook_collection.insert_one(post)
                    print(f"Inserted post with ID: {post['_id']}")

            except errors.DuplicateKeyError:
                print(f"Skipped duplicate post with ID: {post['_id']}")

    else:
        print(f"Error: {response.status_code}")
        print(f"Response: {response}")
        raise Exception('Failed to fetch run data')


if __name__ == "__main__":
    try:
        search_terms_data = get_search_terms()
        
        for search_term in search_terms_data:
            query = search_term['query']
            clientId = search_term['clientId']
            clientName = search_term['clientName']
            companyId = search_term['companyId']
            companyName = search_term['companyName']
            
            run_id = start_actor_and_get_run_id(query)
            print(f'Actor started with run ID: {run_id}')

            # Polling to check if the run has finished
            while not is_run_finished(run_id):
                print('Waiting for actor run to complete...')
                time.sleep(60)  # Wait for 1 minute before checking again

            get_run_data(run_id, query, clientId, clientName, companyId, companyName)
        
    except Exception as e:
        print(f"An error occurred: {e}")
