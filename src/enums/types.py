from enum import Enum


class SearchBy(Enum):
    INFLUENCER = "influencer"
    KEYWORDS = "keywords"
    QUERY = "query"


class Platform(Enum):
    YOUTUBE = "youtube"
    TWITTER = "twitter"
    FACEBOOK = "facebook"
