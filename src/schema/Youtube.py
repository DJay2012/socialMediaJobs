from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, HttpUrl, field_serializer
from src.utils.helper import format_youtube_duration, normalize_to_datetime


class Stats(BaseModel):
    views: int = 0
    likes: int = 0
    comments: int = 0


class Transcripts(BaseModel):
    languageCode: str
    languageName: str
    segments: List[Dict[str, Any]]


class Channel(BaseModel):
    id: str = ""
    name: str = ""


class Tags(BaseModel):
    clientId: str = ""
    clientName: str = ""
    companyId: str = ""
    companyName: str = ""


class VideoSchema(BaseModel):
    _id: str
    title: str
    description: str
    duration: str
    publishedAt: datetime
    thumbnail: Optional[HttpUrl] = None
    link: Optional[HttpUrl] = None
    location: Optional[Dict[str, Any]] = None
    stats: Stats
    channel: Channel
    transcripts: Optional[Dict[str, Transcripts]] = None
    keywords: Optional[List[str]] = []
    tags: Optional[List[Tags]] = []
    language: str = "en"

    model_config = ConfigDict(extra="allow")

    @field_serializer("link", "thumbnail")
    def serialize_url(self, url: HttpUrl, _info):
        return str(url)

    @classmethod
    def from_api(cls, video: Dict[str, Any]) -> "VideoSchema":
        """Factory method to create model from raw API response"""
        snippet = video["snippet"]
        video_stats = video.get("stats", {})
        content_details = video.get("contentDetails", {})

        # Handle both search results (id.videoId) and video details (id as string)
        if isinstance(video["id"], dict):
            _id = video["id"]["videoId"]
        else:
            _id = video["id"]

        title = snippet.get("title", "")
        description = snippet.get("description", "")
        duration = format_youtube_duration(content_details.get("duration", ""))
        publishedAt = normalize_to_datetime(snippet.get("publishedAt"))

        # Handle thumbnail URL safely
        thumbnails = snippet.get("thumbnails", {})
        thumbnail = (
            thumbnails.get("high", {}).get("url")
            or thumbnails.get("medium", {}).get("url")
            or thumbnails.get("default", {}).get("url")
            or None
        )

        link = f"https://www.youtube.com/watch?v={_id}"
        location = video.get("location", None)
        stats = Stats(
            views=int(video_stats.get("viewCount", 0)),
            likes=int(video_stats.get("likeCount", 0)),
            comments=int(video_stats.get("commentCount", 0)),
        )
        channel = Channel(
            id=snippet.get("channelId", ""),
            name=snippet.get("channelTitle", ""),
        )
        transcripts = video.get("transcripts", None)
        keywords = video.get("keywords", [])
        tags = video.get("tags", [])

        if isinstance(transcripts, dict) and transcripts:
            language = next(
                iter(transcripts.keys()), snippet.get("defaultAudioLanguage", "en")
            )

        return cls(
            _id=_id,
            title=title,
            description=description,
            duration=duration,
            publishedAt=publishedAt,
            thumbnail=thumbnail,
            link=link,
            location=location,
            stats=stats,
            channel=channel,
            transcripts=transcripts,
            keywords=keywords,
            tags=tags,
            language=language,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dict (DB insertion ready)"""
        return self.model_dump(by_alias=True, exclude_none=False)


class ChannelSchema(BaseModel):
    _id: str
    title: str
    description: str
    subscribers: int
    username: str
    videos: int
    views: int
    playlistId: str
    thumbnail: Optional[HttpUrl] = None
    publishedAt: datetime

    model_config = ConfigDict(extra="allow")

    @field_serializer("thumbnail")
    def serialize_url(self, url: HttpUrl, _info):
        return str(url)

    @classmethod
    def from_api(cls, channel: Dict[str, Any]) -> "ChannelSchema":
        """Factory method to create model from raw API response"""
        snippet = channel["snippet"]
        statistics = channel.get("statistics", {})
        content_details = channel.get("contentDetails", {})

        # Handle both search results (id.videoId) and video details (id as string)
        if isinstance(channel["id"], dict):
            _id = channel["id"]["channelId"]
        else:
            _id = channel["id"]

        title = snippet.get("title", "")
        description = snippet.get("description", "")
        publishedAt = normalize_to_datetime(snippet.get("publishedAt"))
        username = snippet.get("customUrl", "")

        # Handle thumbnail URL safely
        thumbnails = snippet.get("thumbnails", {})
        thumbnail = (
            thumbnails.get("high", {}).get("url")
            or thumbnails.get("medium", {}).get("url")
            or thumbnails.get("default", {}).get("url")
            or None
        )
        subscribers = int(statistics.get("subscriberCount", 0))
        views = int(statistics.get("viewCount", 0))
        videos = int(statistics.get("videoCount", 0))
        playlistId = content_details.get("relatedPlaylists", {}).get("uploads", "")

        return cls(
            _id=_id,
            title=title,
            description=description,
            username=username,
            subscribers=subscribers,
            videos=videos,
            views=views,
            playlistId=playlistId,
            publishedAt=publishedAt,
            thumbnail=thumbnail,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dict (DB insertion ready)"""
        return self.model_dump(by_alias=True, exclude_none=False)
