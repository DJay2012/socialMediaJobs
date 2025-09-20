from enum import Enum


class Platform(str, Enum):
    YOUTUBE = "youtube"
    TWITTER = "twitter"
    FACEBOOK = "facebook"


class KeywordEntity(str, Enum):
    INFLUENCER = "influencerName"
    KEYWORDS = "keywords"
    QUERY = "query"
