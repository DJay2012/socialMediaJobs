from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, HttpUrl, field_serializer
from utils.helper import normalize_to_datetime


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


class CompanyTag(BaseModel):
    id: str = ""
    name: str = ""


class YoutubeSchema(BaseModel):
    _id: str
    title: str
    description: str
    publishedAt: Optional[datetime] = None
    thumbnail: HttpUrl
    link: HttpUrl
    stats: Optional[Stats] = None
    channel: Optional[Channel] = None
    transcripts: Optional[Dict[str, Transcripts]] = None
    keywords: Optional[List[str]] = None
    companyTag: Optional[List[CompanyTag]] = []

    model_config = ConfigDict(extra="allow")

    @field_serializer("link", "thumbnail")
    def serialize_url(self, url: HttpUrl, _info):
        return str(url)

    @classmethod
    def from_api(cls, video: Dict[str, Any]) -> "YoutubeSchema":
        """Factory method to create model from raw API response"""
        snippet = video["snippet"]

        # Handle both search results (id.videoId) and video details (id as string)
        if isinstance(video["id"], dict):
            _id = video["id"]["videoId"]
        else:
            _id = video["id"]

        title = snippet.get("title", "")
        description = snippet.get("description", "")
        publishedAt = normalize_to_datetime(snippet.get("publishedAt"))

        # Handle thumbnail URL safely
        thumbnails = snippet.get("thumbnails", {})
        thumbnail = (
            thumbnails.get("high", {}).get("url")
            or thumbnails.get("medium", {}).get("url")
            or thumbnails.get("default", {}).get("url")
            or "https://via.placeholder.com/320x180"
        )

        link = f"https://www.youtube.com/watch?v={_id}"
        video_stats = video.get("stats", {})
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
        keywords = video.get("keywords", None)
        companyTag = video.get("companyTag", [])

        return cls(
            _id=_id,
            title=title,
            description=description,
            publishedAt=publishedAt,
            thumbnail=thumbnail,
            link=link,
            stats=stats,
            channel=channel,
            transcripts=transcripts,
            keywords=keywords,
            companyTag=companyTag,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dict (DB insertion ready)"""
        return self.model_dump(by_alias=True, exclude_none=False)
