from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, ConfigDict, HttpUrl, field_serializer
from src.utils.helper import get_transcript_from_doc, normalize_to_datetime
from src.database.operation import (
    get_sequence_id,
    insert_social_feed_tags,
    update_social_feed_id_to_youtube,
)
from src.log.logging import logger

PUBLICATION_ID = "20100424100414211"
PUBLICATION_NAME = "youtube.com"
PUBLICATION_CATEGORY = "Youtube"


class FeedInfo(BaseModel):
    link: str
    isActive: bool = True
    socialFeedType: int


class FeedData(BaseModel):
    headlineSnippet: str
    summarySnippet: str
    headline: str
    summary: str
    text: str
    feedDate: datetime
    feedDateTime: datetime
    articleDateNumber: int
    language: str = "en"


class PublicationInfo(BaseModel):
    id: str = PUBLICATION_ID
    name: str = PUBLICATION_NAME
    publicationCategory: str = PUBLICATION_CATEGORY


class ChannelInfo(BaseModel):
    id: str
    name: str


class CompanyTag(BaseModel):
    id: str
    name: str


class SearchInfo(BaseModel):
    keywordMatched: List[str] = []


class QcEntry(BaseModel):
    name: Optional[str] = None
    on: Optional[datetime] = None


class Qc(BaseModel):
    qc1Status: bool = False
    qc2Status: bool = False
    qc3Status: bool = False
    qc1: List[QcEntry]
    qc2: List[QcEntry]
    qc3: List[QcEntry]


class ImageInfo(BaseModel):
    hasImage: bool
    url: Optional[HttpUrl] = None

    @field_serializer("url")
    def serialize_url(self, url: HttpUrl, _info):
        return str(url) if url else None


class VideoInfo(BaseModel):
    hasVideo: bool
    url: Optional[HttpUrl] = None

    @field_serializer("url")
    def serialize_url(self, url: HttpUrl, _info):
        return str(url) if url else None


class SocialMetrics(BaseModel):
    wordCount: int
    reach: int

    model_config = ConfigDict(extra="allow")


class UploadInfo(BaseModel):
    uploadDate: datetime
    uploadDateNumber: int


class AuditEntry(BaseModel):
    name: str
    on: datetime


class AuditInfo(BaseModel):
    created: AuditEntry
    modified: List[AuditEntry] = []


class LocationInfo(BaseModel):
    continent: Optional[str] = None
    country: Optional[str] = None
    countryCode: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    longitude: Optional[float] = None
    latitude: Optional[float] = None


class Author(BaseModel):
    name: str
    location: LocationInfo


class ExtraSource(BaseModel):
    continent: Optional[str] = None
    country: Optional[str] = None
    countryCode: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    longitude: Optional[float] = None
    latitude: Optional[float] = None


class SocialFeedSchema(BaseModel):
    _id: int
    socialFeedId: int
    feedInfo: FeedInfo
    feedData: FeedData
    publicationInfo: PublicationInfo
    channelInfo: ChannelInfo
    companyTag: List[CompanyTag]
    searchInfo: SearchInfo
    image: ImageInfo
    video: VideoInfo
    socialMetrics: SocialMetrics
    uploadInfo: UploadInfo
    auditInfo: AuditInfo
    socialMediaInfo: Dict[str, Any] = {}
    location: Dict[str, Any] = {}

    model_config = ConfigDict(extra="allow")

    @classmethod
    def from_youtube(
        cls, mongo_doc: Dict[str, Any], social_feed_type: Dict[str, Any]
    ) -> "SocialFeedSchema":
        """Factory method to create model from MongoDB document"""

        # Handle MongoDB numberLong fields
        def extract_number_long(value):
            if isinstance(value, dict) and "$numberLong" in value:
                return int(value["$numberLong"])
            return value

        def extract_date(value):
            if isinstance(value, dict) and "$date" in value:
                return normalize_to_datetime(value["$date"])
            return value

        # Process the document
        processed_doc = {}

        # Extract top-level fields
        social_feed_id = mongo_doc.get("socialFeedId")

        if social_feed_id is None:
            logger.warning(
                f"Social feed id is None for document {mongo_doc.get('_id')}"
            )
            return
            social_feed_id = get_sequence_id("socialFeedId")
            update_social_feed_id_to_youtube(mongo_doc.get("_id"), social_feed_id)
            logger.info(
                f"Updated social feed id to {social_feed_id} for document {mongo_doc.get('_id')}"
            )

        processed_doc["_id"] = social_feed_id
        processed_doc["socialFeedId"] = social_feed_id

        # Process feedInfo
        processed_doc["feedInfo"] = FeedInfo(
            link=mongo_doc.get("link", ""),
            isActive=mongo_doc.get("isActive", True),
            socialFeedType=social_feed_type.get("_id", 1),
        )

        # Process feedData
        published_at = extract_date(mongo_doc.get("publishedAt"))

        # Ensure we have a valid date for the shard key
        if not published_at:
            raise ValueError(
                f"Invalid or missing publishedAt date for document {mongo_doc.get('_id', 'unknown')}"
            )

        article_date_number = (
            int(published_at.strftime("%Y%m%d"))
            if published_at and isinstance(published_at, datetime)
            else 0
        )

        # Set feedDate to midnight of the published date (shard key)
        feed_date = published_at.replace(hour=0, minute=0, second=0, microsecond=0)
        text = get_transcript_from_doc(mongo_doc)

        processed_doc["feedData"] = FeedData(
            headline=mongo_doc.get("title", ""),
            headlineSnippet=mongo_doc.get("title", ""),
            summarySnippet=mongo_doc.get("description", ""),
            summary=mongo_doc.get("description", ""),
            text=text,
            feedDate=feed_date,
            feedDateTime=published_at,
            articleDateNumber=article_date_number,
            language=mongo_doc.get("language", "en"),
        )

        # Process publicationInfo
        processed_doc["publicationInfo"] = PublicationInfo()

        # Process channelInfo
        channel = mongo_doc.get("channel", {})
        processed_doc["channelInfo"] = ChannelInfo(
            id=channel.get("id", ""), name=channel.get("name", "")
        )

        audit_info = AuditInfo(
            created=AuditEntry(
                name="youtubeScraper",
                on=datetime.now(timezone.utc),
            ),
        )

        # Process companyTag
        tags = mongo_doc.get("tags", [])
        company_tags = [
            CompanyTag(id=tag.get("companyId", ""), name=tag.get("companyName", ""))
            for tag in tags
        ]

        processed_doc["companyTag"] = company_tags

        social_feed_tags = []
        for company_tag in company_tags:
            social_feed_tags.append(
                {
                    "_id": f"{social_feed_id}{company_tag.id}",  # Add index to ensure uniqueness
                    "feedDate": published_at,
                    "socialFeedId": social_feed_id,
                    "company": company_tag.model_dump(),
                    "auditInfo": audit_info.model_dump(),
                }
            )
        insert_social_feed_tags(social_feed_tags)

        # Process searchInfo
        keywords = mongo_doc.get("keywords") or []
        processed_doc["searchInfo"] = SearchInfo(keywordMatched=keywords)

        # Process image
        processed_doc["image"] = ImageInfo(
            hasImage=True, url=mongo_doc.get("thumbnail", "")
        )

        # Process video
        processed_doc["video"] = VideoInfo(hasVideo=True, url=mongo_doc.get("link", ""))

        stats = mongo_doc.get("stats", {})

        # Process socialMetrics
        metrics = mongo_doc.get("socialMetrics", {})
        processed_doc["socialMetrics"] = SocialMetrics(
            wordCount=len(text.split()) if isinstance(text, str) else 0,
            reach=metrics.get("reach", 0),
            **stats,
        )

        # Process uploadInfo
        upload_date = datetime.now(timezone.utc)
        upload_date_number = (
            int(upload_date.strftime("%Y%m%d"))
            if upload_date and isinstance(upload_date, datetime)
            else 0
        )
        processed_doc["uploadInfo"] = UploadInfo(
            uploadDate=upload_date,
            uploadDateNumber=upload_date_number,
        )

        # Process auditInfo
        processed_doc["auditInfo"] = audit_info
        processed_doc["location"] = mongo_doc.get("location") or {}

        return cls(**processed_doc)

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dict (DB insertion ready)"""
        return self.model_dump(by_alias=True, exclude_none=False)
