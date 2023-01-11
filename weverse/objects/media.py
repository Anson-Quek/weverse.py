from .attachment import Photo
from .post import PostLike


class MediaLike(PostLike):
    """Represents a Weverse Media.

    Inherits from :class:`.post.PostLike`.

    Shares the same attributes with :class:`.post.PostLike`.

    Inherited by:

    - :class:`ImageMedia`
    - :class:`YoutubeMedia`
    - :class:`WeverseMedia`
    - :class:`.live.Live`

    .. container:: operations

        .. describe:: str(x)

            Returns the media's title.

    Attributes
    ----------
    title: :class:`str`
        The title of the media.
    thumbnail_url: :class:`str`
        The URL of the thumbnail of the media.
    """

    __slots__ = ("title", "thumbnail_url")

    def __init__(self, data: dict):
        super().__init__(data)
        self.title: str = data["title"]
        self.thumbnail_url: str = data["extension"]["mediaInfo"]["thumbnail"]["url"]

    def __repr__(self):
        return f"Media media_id={self.id}, title={self.title}"

    def __str__(self):
        return self.title


class ImageMedia(MediaLike):
    """Represents a Weverse Media that contains images.

    Inherits from :class:`MediaLike`.

    Shares the same attributes with :class:`.post.PostLike` and :class:`MediaLike`.
    """

    @property
    def photos(self) -> list[Photo]:
        """list[:class:`.attachment.Photo`]: A list of :class:`.attachment.Photo`
        objects in the media."""
        return [
            Photo(photo_data)
            for photo_data in self.data["extension"]["image"]["photos"]
        ]


class YoutubeMedia(MediaLike):
    """Represents a Weverse Media that contains a YouTube video.

    Inherits from :class:`MediaLike`.

    Shares the same attributes with :class:`.post.PostLike` and :class:`MediaLike`.

    Attributes
    ----------
    video_duration: :class:`int`
        The duration of the YouTube video, in seconds.
    youtube_url: :class:`str`
        The URL to the YouTube video.
    video_screen_orientation: :class:`str`
        The screen orientation of the video.
    """

    __slots__ = ("video_duration", "youtube_url", "video_screen_orientation")

    def __init__(self, data: dict):
        super().__init__(data)
        self.video_duration: int = data["extension"]["youtube"]["playTime"]
        self.youtube_url: str = data["extension"]["youtube"]["videoPath"]
        self.video_screen_orientation: str = data["extension"]["youtube"][
            "screenOrientation"
        ]


class WeverseMedia(MediaLike):
    """Represents a Weverse Media that contains a Weverse video.

    Inherits from :class:`MediaLike`.

    Shares the same attributes with :class:`.post.PostLike` and :class:`MediaLike`.

    Inherited by:

    - :class:`.live.Live`

    Attributes
    ----------
    video_id: :class:`int`
        The ID of the Weverse video.
    internal_video_id: :class:`str` | :class:`None`
        The internal ID of the Weverse video. Returns :class:`None`
        in the case of a live broadcast that is still broadcasting and not
        converted into a VOD yet.
    video_type: :class:`str`
        The type of Weverse video.
    aired_at: :class:`int`
        The time the Weverse video got aired at, in epoch time.
    is_paid_video: :class:`bool`
        Whether the Weverse video is a paid video.
    is_membership_only_video: :class:`bool`
        Whether the Weverse video is only accessible by users with a
        paid membership to the community the video belongs to.
    video_screen_orientation: :class:`str`
        The screen orientation of the video.
    video_play_count: :class:`int`
        The number of views on the Weverse video.
    video_like_count: :class:`int`
        The number of likes on the Weverse video.
    video_duration: :class:`int` | :class:`None`
        The duration of the Weverse video, in seconds. Returns :class:`None`
        in the case of a live broadcast that is still broadcasting and not
        converted into a VOD yet.
    """

    __slots__ = (
        "video_id",
        "internal_video_id",
        "video_type",
        "aired_at",
        "is_paid_video",
        "is_membership_only_video",
        "video_screen_orientation",
        "video_play_count",
        "video_like_count",
        "video_duration",
    )

    def __init__(self, data: dict):
        super().__init__(data)
        self.video_id: int = data["extension"]["video"]["videoId"]
        self.internal_video_id: str | None = data["extension"]["video"].get(
            "infraVideoId"
        )
        self.video_type: str = data["extension"]["video"]["type"]
        self.aired_at: int = data["extension"]["video"]["onAirStartAt"]
        self.is_paid_video: bool = data["extension"]["video"]["paid"]
        self.is_membership_only_video: bool = data["extension"]["video"][
            "membershipOnly"
        ]
        self.video_screen_orientation: str = data["extension"]["video"][
            "screenOrientation"
        ]
        self.video_play_count: int = data["extension"]["video"]["playCount"]
        self.video_like_count: int = data["extension"]["video"]["likeCount"]
        self.video_duration: int | None = data["extension"]["video"].get("playTime")
