from enum import Enum


class NotificationType(Enum):
    """The enum for Weverse Notification Types."""
    POST = "post"
    ARTIST_POST_COMMENT = "artist_post_comment"
    USER_POST_COMMENT = "user_post_comment"
    MEDIA_COMMENT = "media_comment"
    MOMENT_COMMENT = "moment_comment"
    MOMENT = "moment"
    LIVE = "live"
    NOTICE = "notice"
    MEDIA = "media"
    BIRTHDAY = "birthday"

    def __repr__(self):
        return self.value
