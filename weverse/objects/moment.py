from .attachment import Photo, Video
from .post import PostLike


class MomentLike(PostLike):
    """Represents a Weverse Moment-Like Object.

    Inherits from :class:`.post.PostLike`.

    Shares the same attributes with :class:`.post.PostLike`.

    Inherited by:

    - :class:`Moment`
    - :class:`OldMoment`

    .. container:: operations

        .. describe:: str(x)

            Returns the moment's plain body.

    Attributes
    ----------
    expire_at: :class:`int`
        The time the moment expires at, in epoch.
    """

    __slots__ = ("expire_at",)

    def __init__(self, data: dict):
        super().__init__(data)

        if "moment" in data["extension"]:
            self.expire_at: int = data["extension"]["moment"]["expireAt"]

        else:
            self.expire_at: int = data["extension"]["momentW1"]["expireAt"]

    def __repr__(self):
        return f"Moment moment_id={self.id}, plain_body={self.plain_body}"

    def __str__(self):
        return self.plain_body


class Moment(MomentLike):
    """Represents a Weverse Moment that has been created after their rework.

    Inherits from :class:`MomentLike`.

    Shares the same attributes with :class:`.post.PostLike` and :class:`MomentLike`.

    Attributes
    ----------
    video: :class:`.attachment.Video`
        The :class:`.attachment.Video` object of the video in the moment.
    """

    __slots__ = ("video",)

    def __init__(self, data: dict):
        super().__init__(data)
        self.video: Video = Video(data["extension"]["moment"]["video"])


class OldMoment(MomentLike):
    """Represents a Weverse Moment that has been created before their rework.

    Inherits from :class:`MomentLike`.

    Shares the same attributes with :class:`.post.PostLike` and :class:`MomentLike`.

    Attributes
    ----------
    photo: :class:`.attachment.Photo` | :class:`None`
        The :class:`.attachment.Photo` object of the photo in the moment,
        if the image used in the moment is not a default Weverse background image.
    background_image_url: :class:`str` | :class:`None`
        The URL of the default Weverse background image if it is used.
    """

    __slots__ = ("photo", "background_image_url")

    def __init__(self, data: dict):
        super().__init__(data)
        self.photo: Photo | None = (
            Photo(data["extension"]["momentW1"]["photo"])
            if "photo" in data["extension"]["momentW1"]
            else None
        )
        self.background_image_url: str | None = (
            data["extension"]["momentW1"]["backgroundImageUrl"]
            if "backgroundImageUrl" in data["extension"]["momentW1"]
            else None
        )
