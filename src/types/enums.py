from enum import Enum


class SocialFeedType(str, Enum):
    YOUTUBE = "youtube"
    TWITTER = "twitter"
    FACEBOOK = "facebook"


class Keyword(str, Enum):
    PLAYLIST = "playlistId"
    QUERY = "query"
