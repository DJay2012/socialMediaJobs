from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, HttpUrl
from utils.helper import normalize_to_datetime


class Statistics(BaseModel):
    views: int
    likes: int
    comments: int


class Transcripts(BaseModel):
    languageCode: str
    languageName: str
    segments: List[Dict[str, Any]]


class Channel(BaseModel):
    id: str
    name: str


class CompanyTag(BaseModel):
    id: str
    name: str


class YoutubeSchema(BaseModel):
    _id: str
    title: str
    description: str
    publishedAt: Optional[datetime] = None
    thumbnail: HttpUrl
    link: HttpUrl
    stats: Optional[Statistics] = None
    channel: Optional[Channel] = None
    transcripts: Optional[Dict[str, Transcripts]] = None
    matchedKeywords: Optional[List[str]] = []
    companyTag: Optional[List[CompanyTag]] = []

    @classmethod
    def from_api(cls, video: Dict[str, Any]) -> "YoutubeSchema":
        """Factory method to create model from raw API response"""
        snippet = video["snippet"]
        publishedAt = snippet.get("publishedAt")

        return cls(
            _id=video["id"]["videoId"],
            title=snippet["title"],
            description=snippet["description"],
            publishedAt=normalize_to_datetime(publishedAt),
            thumbnail=video["snippet"]["thumbnails"]["high"]["url"],
            link=f"https://www.youtube.com/watch?v={video['id']['videoId']}",
            stats=video.get("stats"),
            channel=Channel(
                id=video.get("channel", {}).get("id"),
                name=video.get("channel", {}).get("name"),
                profile_image=video.get("channel", {}).get("profile_image"),
                location=video.get("channel", {}).get("location"),
            ),
            transcripts=video.get("transcripts"),
            matchedKeywords=video.get("matchedKeywords"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dict (DB insertion ready)"""
        return self.model_dump(by_alias=True)
