from enum import Enum


class Platform(Enum):
    YOUTUBE = "youtube"
    TWITTER = "twitter"
    FACEBOOK = "facebook"


class KeywordEntity(Enum):
    INFLUENCER = "influencerName"
    KEYWORDS = "keywords"
    QUERY = "query"
