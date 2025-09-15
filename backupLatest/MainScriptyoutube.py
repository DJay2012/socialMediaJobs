import requests
import json
from pymongo import MongoClient
import pytz
from datetime import datetime

# API_KEY = 'AIzaSyBCmfIHRbtzZTeUHcBnjhcRCm5LHogSDhk'
API_KEY = "AIzaSyC_4vnHyPBYw0aLmnDm106IrJn6W604XGk"
maxResults = 20

# MongoDB connection setup
mongo_client = MongoClient("mongodb://admin:Cir%5EPnq%406A@51.195.235.59:27017/")
mongo_db = mongo_client["smFeeds"]
mongo_collection = mongo_db["youtube"]
search_keywords_collection = mongo_db["searchKeywords"]


# Function to fetch search terms from MongoDB with filtering by clientId and type
def get_search_terms(client_id_filter="MHADA11"):
    query = {"type": "youtube", "clientId": client_id_filter}

    documents = search_keywords_collection.find(query)
    search_terms_data = []
    for doc in documents:
        search_terms_data.append(
            {
                "query": doc.get("query", ""),
                "clientId": doc.get("clientId", ""),
                "clientName": doc.get("clientName", ""),
                "companyId": doc.get("companyId", ""),
                "companyName": doc.get("CompanyName", ""),
            }
        )
    return search_terms_data


# Function to fetch YouTube data based on search query
def fetch_youtube_data(api_key, query, max_results, page_token=None):
    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&maxResults={max_results}&q={query}&regionCode=IN&key={api_key}"
    if page_token:
        url += f"&pageToken={page_token}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to retrieve data: {response.status_code}")
        return None


# Function to fetch video details from YouTube
def fetch_video_details(api_key, video_ids):
    url = f'https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics,contentDetails&id={",".join(video_ids)}&key={api_key}'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to retrieve video details: {response.status_code}")
        return None


# Function to fetch channel details from YouTube
def fetch_channel_details(api_key, channel_ids):
    url = f'https://www.googleapis.com/youtube/v3/channels?part=snippet,statistics&id={",".join(channel_ids)}&key={api_key}'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to retrieve channel details: {response.status_code}")
        return None


# Function to parse published_at to UTC datetime
def parse_published_at(published_at):
    tz = pytz.UTC
    try:
        return datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%S.%fZ").replace(
            tzinfo=tz
        )
    except ValueError:
        return datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=tz)


# Main function to run the YouTube search and save results to MongoDB
def main():
    search_terms_data = get_search_terms()  # This will filter for clientId "MHADA11"

    for search_term in search_terms_data:
        query = search_term["query"]
        clientId = search_term["clientId"]
        clientName = search_term["clientName"]
        companyId = search_term["companyId"]
        companyName = search_term["companyName"]

        print(f"Running query for {companyId}...")

        page_token = None
        while True:
            search_data = fetch_youtube_data(API_KEY, query, maxResults, page_token)

            if not search_data:
                break

            video_ids = [
                item["id"]["videoId"]
                for item in search_data.get("items", [])
                if item["id"]["kind"] == "youtube#video"
            ]
            channel_ids = list(
                set(
                    item["snippet"]["channelId"]
                    for item in search_data.get("items", [])
                )
            )

            if not video_ids:
                print("No video IDs found.")
                break

            video_details = fetch_video_details(API_KEY, video_ids)
            channel_details = fetch_channel_details(API_KEY, channel_ids)

            if not video_details or not channel_details:
                break

            channel_info = {}
            for channel in channel_details.get("items", []):
                channel_info[channel["id"]] = {
                    "profile_image": channel["snippet"]["thumbnails"]["default"]["url"],
                    "location": channel["snippet"].get("country", "Unknown"),
                }

            for item in search_data.get("items", []):
                if item["id"]["kind"] == "youtube#video":
                    video_id = item["id"]["videoId"]
                    video_info = next(
                        (
                            video
                            for video in video_details.get("items", [])
                            if video["id"] == video_id
                        ),
                        {},
                    )

                    item["statistics"] = video_info.get("statistics", {})
                    channel_id = item["snippet"]["channelId"]
                    item["profile_image"] = channel_info.get(channel_id, {}).get(
                        "profile_image"
                    )
                    item["location"] = channel_info.get(channel_id, {}).get("location")
                    item["video_link"] = f"https://www.youtube.com/watch?v={video_id}"

                    item["_id"] = video_id
                    item["keywords"] = query
                    item["createdAt"] = parse_published_at(
                        item["snippet"]["publishedAt"]
                    )

                    # Add key tag with client and company details in an array of objects
                    item["tags"] = [
                        {
                            "clientId": clientId,
                            "clientName": clientName,
                            "companyId": companyId,
                            "companyName": companyName,
                        }
                    ]

                    mongo_collection.update_one(
                        {"_id": video_id}, {"$set": item}, upsert=True
                    )

            page_token = search_data.get("nextPageToken")
            if not page_token:
                print(f"No more pages to fetch for {companyId}.")
                break

            print(f"Next Page Token for {companyId}: {page_token}")


if __name__ == "__main__":
    main()
