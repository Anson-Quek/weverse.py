import re

from .attachment import Photo


class Notice:
    """Represents a Weverse Notice.

    .. container:: operations

        .. describe:: x == y

            Checks if two notice objects are equal.

        .. describe:: x != y

            Checks if two notice objects are not equal.

        .. describe:: hash(x)

            Returns the notice's hash.

        .. describe:: str(x)

            Returns the notice's plain body.

    Attributes
    ----------
    data: :class:`dict`
        The raw data directly taken from the response generated by Weverse's API.
    id: :class:`int`
        The ID of the notice.
    title: :class:`str`
        The title of the notice.
    body: :class:`str`
        The body that is displayed on the https://weverse.io website.
        Consider using :attr:`plain_body` if you do not want markdowns
        and unnecessary information.
    plain_body: :class:`str`
        The plain body of the notice that does not have markdowns
        and unnecessary information.
    url: :class:`str`
        The URL that leads to the notice.
    is_exposed: :class:`bool`
        Whether the notice is exposed.
    is_published: :class:`bool`
        Whether the notice is published.
    is_hidden_from_artist: :class:`bool`
        Whether the notice is hidden from artists.
    is_membership_only: :class:`bool`
        Whether the notice can only be seen by users who have a
        paid membership in the community the notice belongs to.
    is_pinned: :class:`bool`
        Whether the notice is pinned.
    published_at: :class:`int`
        The time the notice got created at, in epoch.
    notice_type: :class:`str`
        The type of notice it is.
    exposed_status: :class:`str`
        The exposed status of the notice.
    """

    __slots__ = (
        "data",
        "id",
        "title",
        "body",
        "plain_body",
        "url",
        "is_exposed",
        "is_published",
        "is_hidden_from_artist",
        "is_membership_only",
        "is_pinned",
        "published_at",
        "notice_type",
        "exposed_status",
    )

    def __init__(self, data: dict):
        self.data: dict = data
        self.id: int = data["noticeId"]
        self.title: str = data["title"]
        self.body: str = data["body"]
        self.plain_body: str = data["plainBody"]
        self.url: str = data["shareUrl"]
        self.is_exposed: bool = data["exposed"]
        self.is_published: bool = data["published"]
        self.is_hidden_from_artist: bool = data["hideFromArtist"]
        self.is_membership_only: bool = data["membershipOnly"]
        self.is_pinned: bool = data["pinned"]
        self.published_at: int = data["publishAt"]
        self.notice_type: str = data["noticeType"]
        self.exposed_status: str = data["exposedStatus"]

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.id == other.id

        raise NotImplementedError

    def __hash__(self):
        return hash(self.id)

    def __repr__(self):
        return f"Notice notice_id={self.id}, plain_body={self.plain_body}"

    def __str__(self):
        return self.plain_body

    @property
    def photos(self) -> list[Photo]:
        """list[:class:`.attachment.Photo`]: A list of :class:`.attachment.Photo`
        objects in the notice.
        Returns an empty list if there are no photos.
        """
        if not self.data["attachment"].get("photo"):
            return []

        return [
            Photo(photo_data)
            for photo_data in self.data["attachment"]["photo"].values()
        ]

    @property
    def community_id(self) -> int:
        """:class:`int`: The community ID of the community the notice
        belongs to.
        """
        pattern = re.compile(r"([^a-z -][\d]*)")
        match = re.search(pattern, self.data["parentId"])
        return int(match.group(0))
