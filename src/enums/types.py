from enum import Enum


class Platform(str, Enum):
    YOUTUBE = "youtube"
    YOUTUBE_BMW = "youtubeBmw"
    TWITTER = "twitter"
    FACEBOOK = "facebook"


class KeywordEntity(str, Enum):
    PLAYLIST = "playlistId"
    QUERY = "query"
