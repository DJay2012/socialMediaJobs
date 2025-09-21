from enum import Enum


class Platform(str, Enum):
    YOUTUBE = "youtube"
    TWITTER = "twitter"
    FACEBOOK = "facebook"


class KeywordEntity(str, Enum):
    CHANNEL = "channelId"
    QUERY = "query"
