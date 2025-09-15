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
# API_KEY = "AIzaSyC_4vnHyPBYw0aLmnDm106IrJn6W604XGk"
# API_KEY = "AIzaSyAemkCqsAp1N8Jg9ak_UMqXqDYIlaA-ytw"
API_KEY = "AIzaSyAemkCqsAp1N8Jg9ak_UMqXqDYIlaA-ytw"


# MongoDB connection details
MONGO_URI = "mongodb://admin:Cir%5EPnq%246A@57.128.169.41:27017/"
DB_NAME = "xFeeds"
YOUTUBE_COLLECTION = "youtubeWithChannel"

# List of YouTube channels to search
youtubeChannels = [
    "India Today",
    "CNBC-TV18",
    "Times Drive",
    "The Indian Express",
    "Zee News",
    "CNBC Awaaz",
    "News 18 India",
    "Moneycontrol",
    "India.com",
    "Motoroctane",
    "Faisal Khan",
    "Motoroids",
    "Evo India",
    "Acko Drive",
    "Autox",
    "TOI Auto",
    "Carandbike",
    "HT Auto",
    "Auto Live",
    "NDTV Auto",
    "Overdrive",
    "Auto Today",
    "Motor World India",
    "Namaste Car",
    "Bikewale",
    "Jagra HiTech",
    "Power Drift",
    "Fast FWD",
    "Autocar India",
    "Rekhta",
    "The Print",
    "Times Drive Green",
    "Car India",
    "Gear Fliq",
    "Carwale",
    "Drive Spark",
    "Vishal Ahlawat",
    "Top Gear Mag India",
    "Mashable India",
    "Zig Wheels",
    "Motoring World",
    "Bike Dekho",
    "Car Dekho",
    "Motorbeam",
    "Turbocharged Magazine",
    "The UnbiasedblogTV",
    "Sagar Sheldekar",
    "Gear Up with Garima",
    "Carwale Hindi",
    "What Car? India",
    "Rajni Choudhary",
    "Gagan Choudhary",
    "Ayush SSM",
    "Team-BHP",
    "Turn Off Speed",
    "Shifting Gears",
    "Rush Lane",
    "Mobility Outlook",
    "Cartrade.com",
    "ET Auto",
    "Indian Torque",
]

# MongoDB client setup
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
youtube_collection = db[YOUTUBE_COLLECTION]


def get_channel_id(youtube, channelName):
    """Retrieve the channel ID for a given channel name."""
    request = youtube.search().list(
        q=channelName, part="snippet", type="channel", maxResults=1
    )
    response = request.execute()

    if response["items"]:
        channel_id = response["items"][0]["snippet"]["channelId"]
        return channel_id
    else:
        print(f"Channel '{channelName}' not found.")
        return None


def get_channel_videos(youtube, channel_id):
    """Retrieve videos from a specific channel."""
    videos = []
    request = youtube.search().list(
        channelId=channel_id, part="snippet", maxResults=50, order="date"
    )
    response = request.execute()

    videos.extend(response["items"])

    while "nextPageToken" in response:
        request = youtube.search().list(
            channelId=channel_id,
            part="snippet",
            maxResults=50,
            pageToken=response["nextPageToken"],
            order="date",
        )
        response = request.execute()
        videos.extend(response["items"])

    return videos


def get_video_statistics(youtube, video_id):
    """Retrieve video statistics and location."""
    request = youtube.videos().list(part="statistics,recordingDetails", id=video_id)
    response = request.execute()

    if response["items"]:
        stats = response["items"][0]["statistics"]
        location = (
            response["items"][0]
            .get("recordingDetails", {})
            .get("location", "No location available")
        )
        return stats, location
    else:
        return None, None


def get_video_transcript(video_id):
    """Retrieve video transcript."""
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return transcript
    except Exception as e:
        return f"Transcript not available: {str(e)}"


def parse_published_at(published_at):
    """Parse the published date."""
    tz = pytz.UTC
    try:
        return datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%S.%fZ").replace(
            tzinfo=tz
        )
    except ValueError:
        return datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=tz)


def process_channel_videos(youtube, channelName):
    """Process and store videos from a specific channel."""
    channel_id = get_channel_id(youtube, channelName)

    if channel_id:
        videos = get_channel_videos(youtube, channel_id)

        for video in videos:
            try:
                video_id = video["id"]["videoId"]
                title = video["snippet"]["title"]
                description = video["snippet"]["description"]
                publish_date = video["snippet"]["publishedAt"]
                thumbnail = video["snippet"]["thumbnails"]["high"]["url"]
                video_link = f"https://www.youtube.com/watch?v={video_id}"

                stats, location = get_video_statistics(youtube, video_id)
                transcript = get_video_transcript(video_id)

                youtube_data = {
                    "_id": video_id,
                    "channelName": channelName,
                    "video_title": title,
                    "video_description": description,
                    "createdAt": parse_published_at(publish_date),
                    "thumbnail_url": thumbnail,
                    "video_link": video_link,
                    "statistics": {
                        "view_count": stats.get("viewCount", "Not available"),
                        "like_count": stats.get("likeCount", "Not available"),
                        "comment_count": stats.get("commentCount", "Not available"),
                    },
                    "location": location,
                    "transcript": transcript,
                }

                # Upsert the video data
                youtube_collection.replace_one(
                    {"_id": video_id}, youtube_data, upsert=True
                )
                print(f"Processed video: {title}")

            except Exception as e:
                print(f"Error processing video from {channelName}: {e}")
    else:
        print(f"Channel '{channelName}' not found.")


def main():
    """Main function to process YouTube channels and retrieve their videos."""
    youtube = build("youtube", "v3", developerKey=API_KEY)

    for channel in youtubeChannels:
        try:
            process_channel_videos(youtube, channel)

            # Add a random delay between 2 and 5 seconds between each channel processing
            time.sleep(random.uniform(2, 5))

        except HttpError as e:
            print(f"An error occurred for channel {channel}: {e}")
            # If an error occurs, especially rate limit, wait before retrying
            time.sleep(60)


if __name__ == "__main__":
    main()
