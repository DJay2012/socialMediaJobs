from googleapiclient.discovery import build
from pymongo import MongoClient
from youtube_transcript_api import YouTubeTranscriptApi
import pytz
from datetime import datetime
import time
import random
from googleapiclient.errors import HttpError

# API_KEY = "AIzaSyDBEWFE-sR0kQCL8eAWX7RDOBZfG7f3c9I"
# API_KEY = "AIzaSyAtmlelzozWW3naCA6MduOZLydNZdt-eTA"
# API_KEY = "AIzaSyBCmfIHRbtzZTeUHcBnjhcRCm5LHogSDhk"
API_KEY = "AIzaSyC_4vnHyPBYw0aLmnDm106IrJn6W604XGk"
#API_KEY = "AIzaSyAemkCqsAp1N8Jg9ak_UMqXqDYIlaA-ytw"



MONGO_URI = "mongodb://admin:Cir%5EPnq%406A@51.195.235.59:27017/"
DB_NAME = "smFeeds"
SEARCH_COLLECTION = "searchKeywords"
YOUTUBE_COLLECTION = "youtube"


client = MongoClient(MONGO_URI)
db = client[DB_NAME]
search_keywords_collection = db[SEARCH_COLLECTION]
youtube_collection = db[YOUTUBE_COLLECTION]

def get_channel_id(youtube, channel_name):
    request = youtube.search().list(
        q=channel_name,
        part="snippet",
        type="channel",
        maxResults=1
    )
    response = request.execute()
    
    if response['items']:
        channel_id = response['items'][0]['snippet']['channelId']
        return channel_id
    else:
        print(f"Channel '{channel_name}' not found.")
        return None

def get_channel_videos(youtube, channel_id):
    videos = []
    request = youtube.search().list(
        channelId=channel_id,
        part="snippet",
        maxResults=50,
        order="date"
    )
    response = request.execute()
    
    videos.extend(response['items'])
    
    while 'nextPageToken' in response:
        request = youtube.search().list(
            channelId=channel_id,
            part="snippet",
            maxResults=50,
            pageToken=response['nextPageToken'],
            order="date"
        )
        response = request.execute()
        videos.extend(response['items'])
    
    return videos

def get_video_statistics(youtube, video_id):
    request = youtube.videos().list(
        part="statistics, recordingDetails",
        id=video_id
    )
    response = request.execute()
    
    if response['items']:
        stats = response['items'][0]['statistics']
        location = response['items'][0].get('recordingDetails', {}).get('location', "No location available")
        return stats, location
    else:
        return None, None

def get_video_transcript(video_id):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return transcript
    except Exception as e:
        return f"Transcript not available: {str(e)}"

def parse_published_at(published_at):
    tz = pytz.UTC
    try:
        return datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=tz)
    except ValueError:
        return datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=tz)

def search_influencer_in_channel(channel_name, influencer_name, clientid, clientName, companyid, CompanyName):
    youtube = build('youtube', 'v3', developerKey=API_KEY)
    
    channel_id = get_channel_id(youtube, channel_name)
    
    if channel_id:
        videos = get_channel_videos(youtube, channel_id)
        
        filtered_videos = [
            video for video in videos 
            if influencer_name.lower() in video['snippet']['title'].lower() 
            or influencer_name.lower() in video['snippet']['description'].lower()
        ]
        
        if filtered_videos:
            for video in filtered_videos:
                video_id = video['id']['videoId']
                title = video['snippet']['title']
                description = video['snippet']['description']
                publish_date = video['snippet']['publishedAt']
                thumbnail = video['snippet']['thumbnails']['high']['url']
                video_link = f"https://www.youtube.com/watch?v={video_id}"
                
                stats, location = get_video_statistics(youtube, video_id)
                transcript = get_video_transcript(video_id)
                
               
                youtube_data = {
                    "_id": video_id,
                    "channel_name": channel_name,
                    "influencer_name": influencer_name,
                    "tags": [
                        {
                            "clientId": clientid,
                            "clientName": clientName,
                            "companyId": companyid,
                            "companyName": CompanyName
                        }
                    ],
                    "video_title": title,
                    "video_description": description,
                    "createdAt": parse_published_at(publish_date),
                    "thumbnail_url": thumbnail,
                    "video_link": video_link,
                    "statistics": {
                        "view_count": stats['viewCount'],
                        "like_count": stats.get('likeCount', 'Not available'),
                        "comment_count": stats.get('commentCount', 'Not available')
                    },
                    "location": location,
                    "transcript": transcript
                }
                
               
                existing_document = youtube_collection.find_one({"_id": video_id})
                
                if existing_document:
                    # Compare statistics
                    existing_stats = existing_document.get("statistics", {})
                    if (existing_stats.get("view_count") != stats['viewCount'] or
                        existing_stats.get("like_count") != stats.get('likeCount', 'Not available') or
                        existing_stats.get("comment_count") != stats.get('commentCount', 'Not available')):
                        
                        # Update statistics
                        youtube_collection.update_one(
                            {"_id": video_id},
                            {"$set": {"statistics": youtube_data["statistics"]}}
                        )
                        print(f"Updated statistics for video ID: {video_id}")
                    else:
                        print(f"No changes in statistics for video ID: {video_id}")
                else:
                    # Insert the new video data 
                    youtube_collection.insert_one(youtube_data)
                    print(f"Inserted new video data for video ID: {video_id}")
        else:
            print(f"No videos found for influencer '{influencer_name}' in channel '{channel_name}'.")
    else:
        print(f"Channel '{channel_name}' not found.")



def process_keywords():
    
    keywords = search_keywords_collection.find({"type": "youtubeBmw"})
    
    for keyword in keywords:
        channel_name = keyword['channel_name']
        influencer_name = keyword['influencer_name']
        clientId = keyword['clientid']
        clientName = keyword['clientName']
        companyId = keyword['companyid']
        companyName = keyword['CompanyName']
        
        try:
            search_influencer_in_channel(channel_name, influencer_name, clientId, clientName, companyId, companyName)
        except HttpError as e:
            print(f"An error occurred: {e}")
            # If an error occurs, especially rate limit, wait before retrying
            time.sleep(60)
        
        # Add a random delay between 2 and 5 seconds between each keyword processing
        time.sleep(random.uniform(2, 5))

if __name__ == "__main__":
    process_keywords()
