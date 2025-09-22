from enum import Enum


class Platform(str, Enum):
    YOUTUBE = "youtube"
    YOUTUBE_BMW = "youtubeBmw"
    TWITTER = "twitter"
    FACEBOOK = "facebook"


class KeywordEntity(str, Enum):
    CHANNEL = "channelId"
    QUERY = "query"
