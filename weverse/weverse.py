import asyncio
import logging

from .enums import NotificationType
from .errors import NotFound, Forbidden
from .fetcher import WeverseFetcher
from .objects.comment import Comment
from .objects.community import Community, PartialCommunity
from .objects.live import Live
from .objects.media import ImageMedia, WeverseMedia, YoutubeMedia
from .objects.member import Artist, Member
from .objects.moment import Moment, OldMoment
from .objects.notice import Notice
from .objects.notification import Notification
from .objects.post import Post
from .url import get_current_epoch_time
from .utils import MISSING

logger = logging.getLogger(__name__)


class WeverseClient:
    """The Weverse Client that interacts with the official Weverse API.

    Attributes
    ----------
    email: :class:`str`
        The email of the Weverse account to login with.
    password: :class:`str`
        The password of the Weverse account to login with.
    stream_interval: :class:`float`
        The interval in querying the Weverse API for new notifications, in seconds.
    """

    def __init__(
        self,
        email: str,
        password: str,
        stream_interval: float = 20,
    ):
        self.email: str = email
        self.password: str = password
        self.stream_interval: float = stream_interval

        self.__fetcher: WeverseFetcher = WeverseFetcher(self.login_payload)
        self.__cache: _WeverseCache = _WeverseCache()
        self.__task: asyncio.Task = MISSING

    @property
    def login_payload(self) -> dict:
        """:class:`dict`: Returns the login payload used to login to Weverse."""
        return {"email": self.email, "password": self.password}

    async def fetch_latest_notifications(self) -> list[Notification]:
        """Fetches the latest notifications from Weverse's API.

        Returns
        -------
        list[:class:`.notification.Notification`]
            A list that contains the :class:`.notification.Notification` objects
            of the latest Weverse notifications.
        """
        data = await self.__fetcher.fetch_latest_notifications()
        data = data["data"]
        notifications = [
            Notification(notification_data)
            for notification_data in data
            if "community" in notification_data
        ]
        return notifications

    async def fetch_notification(self, notification_id: int) -> Notification:
        """Fetches a Weverse Notification from Weverse's API using its ID.

        Parameters
        ----------
        notification_id: :class:`int`
            The notification ID of the notification to fetch.

        Returns
        -------
        :class:`.notification.Notification`
            The :class:`.notification.Notification` object of the requested
            Weverse Notification.

        Raises
        ------
        NotFound
            If the requested Weverse Notification does not exist.
        """
        data = await self.__fetcher.fetch_notification(notification_id)
        return Notification(data)

    async def fetch_new_notifications(self) -> tuple[list[Notification], list[Comment]]:
        """Fetches the list of new Weverse Notifications from all
        communities that the signed-in account has access to.

        Returns
        -------
        tuple[list[:class:`.notification.Notification`], list[:class:`.comment.Comment`]]
            A tuple that contains a list of new :class:`.notification.Notification`
            objects and a list of new :class:`.comment.Comment` objects.

        Notes
        -----
        The reason why :class:`.comment.Comment` objects are returned for comment-related
        notifications and not :class:`.notification.Notification` objects is because Weverse
        does not provide an easy way to determine which comment-related
        notifications are new. As such, in the post-processing of
        comment-related notifications, the actual :class:`.comment.Comment`
        objects have to be fetched so that we know which comments are new.
        """
        old_non_comment_noti = dict(self.__cache.notification_cache)
        old_comment_noti = dict(self.__cache.comment_notification_cache)

        latest_notifications = await self.fetch_latest_notifications()
        (
            latest_non_comment_noti,
            latest_comment_noti,
        ) = self.__sort_notifications(latest_notifications)

        new_non_comment_noti = self._get_new_non_comment_noti(
            old_non_comment_noti, latest_non_comment_noti
        )

        new_artist_comments = await self._get_new_comment(
            old_comment_noti, latest_comment_noti
        )

        return new_non_comment_noti, new_artist_comments

    def __sort_notifications(
        self, notifications: list[Notification]
    ) -> tuple[list[Notification], list[Notification]]:
        """Sorts a dictionary containing notification data into
        comment notifications and non-comment notifications.

        Parameters
        ----------
        notifications: list[:class:`Notification`]
            The list that contains the :class:`Notification` objects of the
            notifications to sort.

        Returns
        -------
        tuple[list[:class:`Notification`], list[:class:`Notification`]]
            A tuple that contains a list of non-comment notifications and
            a list of comment notifications.
        """
        comment_notification_types = [
            NotificationType.USER_POST_COMMENT,
            NotificationType.MEDIA_COMMENT,
            NotificationType.MOMENT_COMMENT,
            NotificationType.ARTIST_POST_COMMENT,
        ]
        non_comment_notifications = []
        comment_notifications = []

        for notification in notifications:
            if notification.post_type in comment_notification_types:
                self.__cache.cache_comment_noti(notification)
                comment_notifications.append(notification)

            else:
                self.__cache.cache_notification(notification)
                non_comment_notifications.append(notification)

        return non_comment_notifications, comment_notifications

    @staticmethod
    def _get_new_non_comment_noti(
        old_cache: dict[int, Notification], notifications: list[Notification]
    ) -> list[Notification]:
        """Returns a list of new non-comment notifications that do not exist in
        the cache.

        Parameters
        ----------
        old_cache: dict[:class:`int`, :class:`Notificiation`]
            The old notification cache used to check which notifications are new.
        notifications: list[:class:`Notification`]
            The list that contains the latest notifications the user has access to.

        Returns
        -------
        list[:class:`Notification`]
            A list of new notifications.
        """
        current_epoch_time = get_current_epoch_time()
        epoch_time_difference = 600000  # Equivalent to 10 minutes.
        return [
            notification
            for notification in notifications
            if notification.id not in old_cache
            and current_epoch_time - notification.time_created <= epoch_time_difference
        ]

    async def _get_new_comment(
        self, old_cache: dict[str, int], notifications: list[Notification]
    ) -> list[Comment]:
        """Returns a list of new artist comments.

        Parameters
        ----------
        old_cache: dict[:class:`str`, :class:`int`]
            The old notification cache used to check which notifications are new.
        notifications: list[:class:`Notification`]
            The list that contains the latest notifications the user has access to.

        Returns
        -------
        list[:class:`Comment`]
            A list of :class:`Comment` objects of the new
            artist comments.
        """
        new_artist_comments = []
        current_epoch_time = get_current_epoch_time()
        epoch_time_difference = 60000  # Equivalent to 1 minute

        for notification in notifications:
            await asyncio.sleep(0.35)

            try:
                artist_comments = await self.fetch_artist_comments(notification.post_id)

            except NotFound:  # This is because the Post has been deleted.
                continue

            if not old_cache.get(notification.post_id + notification.author.id):
                for artist_comment in artist_comments:
                    if (
                        current_epoch_time - artist_comment.created_at
                        <= epoch_time_difference
                    ) and artist_comment.id not in self.__cache.comment_cache:
                        new_artist_comments.insert(0, artist_comment)
                        self.__cache.cache_comment(artist_comment)

            else:
                # This is done because there can be different artists that
                # have written on a post. As such, a new list is created
                # to contain only comments written by the author provided in
                # the notification data.
                artist_comments = [
                    artist_comment
                    for artist_comment in artist_comments
                    if artist_comment.author.id == notification.author.id
                ]
                comment_count = old_cache[notification.post_id + notification.author.id]
                new_comment_count = notification.count - comment_count

                for artist_comment in artist_comments[0:new_comment_count]:
                    if artist_comment.id not in self.__cache.comment_cache:
                        new_artist_comments.insert(0, artist_comment)
                        self.__cache.cache_comment(artist_comment)

        return new_artist_comments

    async def fetch_joined_communities(self) -> list[PartialCommunity]:
        """Fetches the joined communities from Weverse's API.

        Returns
        -------
        list[:class:`.community.PartialCommunity`]
            A list that contains the :class:`.community.PartialCommunity` objects
            of the joined Weverse communities.

        Notes
        -----
        If more information is required about the communities, you can
        make use of the :meth:`fetch_community()` method.
        """
        data = await self.__fetcher.fetch_joined_communities()
        data = data["data"]
        communities = [PartialCommunity(community_data) for community_data in data]
        return communities

    async def fetch_community(self, community_id: int) -> Community:
        """Fetches a Weverse Community from Weverse's API using its ID.

        Parameters
        ----------
        community_id: :class:`int`
            The community ID of the community to fetch.

        Returns
        -------
        :class:`.community.Community`
            The :class:`.community.Community` object of the requested Weverse
            Community.

        Raises
        ------
        Forbidden
            If the signed in account has not joined the requested Weverse Community.
        NotFound
            If the requested Weverse Community does not exist.
        """
        data = await self.__fetcher.fetch_community(community_id)
        return Community(data)

    async def fetch_artists(self, community_id: int) -> list[Artist]:
        """Fetches a list of artists that belong to a Weverse Community
        from Weverse's API using the community ID.

        Parameters
        ----------
        community_id: :class:`int`
            The community ID of the community to fetch the artists from.

        Returns
        -------
        list[:class:`.member.Artist`]
            A list that contains the :class:`.member.Artist` objects of the specified
            Weverse community.

        Raises
        ------
        Forbidden
            If the signed in account has not joined the requested Weverse Community.
        NotFound
            If the requested Weverse Community does not exist.
        """
        data = await self.__fetcher.fetch_artists(community_id)
        artists = [Artist(artist_data) for artist_data in data]
        return artists

    async def fetch_post(self, post_id: str) -> Post:
        """Fetches a Weverse Post from Weverse's API using its ID.

        Parameters
        ----------
        post_id: :class:`str`
            The post ID of the post to fetch.

        Returns
        -------
        :class:`.post.Post`
            The :class:`.post.Post` object of the requested Weverse Post.

        Raises
        ------
        Forbidden
            If the signed in account has not joined the requested Weverse Community
            the post belongs to.
        NotFound
            If the requested Weverse Post does not exist.
        """
        data = await self.__fetcher.fetch_post(post_id)
        return Post(data)

    async def fetch_media(
        self, media_id: str
    ) -> ImageMedia | WeverseMedia | YoutubeMedia:
        """Fetches a Weverse Media from Weverse's API using its ID.

        Parameters
        ----------
        media_id: :class:`str`
            The media ID of the media to fetch.

        Returns
        -------
        :class:`.media.ImageMedia` | :class:`.media.WeverseMedia` | :class:`.media.YoutubeMedia`
            Can be either a :class:`.media.ImageMedia`, :class:`.media.WeverseMedia` or
            :class:`.media.YoutubeMedia` object of the requested Weverse Media depending
            on the type of media it is.

        Raises
        ------
        Forbidden
            If the signed in account has not joined the requested Weverse Community
            the media belongs to.
        NotFound
            If the requested Weverse Media does not exist.
        """
        data = await self.__fetcher.fetch_post(media_id)

        if "image" in data["extension"]:
            return ImageMedia(data)

        if "video" in data["extension"]:
            return WeverseMedia(data)

        return YoutubeMedia(data)

    async def fetch_live(self, live_id: str) -> Live:
        """Fetches a Weverse Live Broadcast from Weverse's API using its ID.

        Parameters
        ----------
        live_id: :class:`str`
            The live ID of the live broadcast to fetch.

        Returns
        -------
        :class:`.live.Live`
            The :class:`.live.Live` object of the requested Weverse Live Broadcast

        Raises
        ------
        Forbidden
            If the signed in account has not joined the requested Weverse Community
            the live broadcast belongs to.
        NotFound
            If the requested Weverse Live Broadcast does not exist.
        """
        data = await self.__fetcher.fetch_post(live_id)
        return Live(data)

    async def fetch_moment(self, moment_id: str) -> Moment | OldMoment:
        """Fetches a Weverse Moment from Weverse's API using its ID.

        Parameters
        ----------
        moment_id: :class:`str`
            The moment ID of the moment to fetch.

        Returns
        -------
        :class:`.moment.Moment` | :class:`.moment.OldMoment`
            The :class:`.moment.Moment` or :class:`.moment.OldMoment` object
            of the requested Weverse moment depending on the type of moment it is.

        Raises
        ------
        Forbidden
            If the signed in account has not joined the requested Weverse Community
            the moment belongs to.
        NotFound
            If the requested Weverse Moment does not exist.
        """
        data = await self.__fetcher.fetch_post(moment_id)

        if "moment" in data["extension"]:
            return Moment(data)

        return OldMoment(data)

    async def fetch_video_url(self, video_id: str) -> str:
        """Fetches a Weverse Post Video URL by its ID.

        Parameters
        ----------
        video_id: :class:`str`
            The ID of the video to fetch.

        Returns
        -------
        :class:`str`
            The URL of the video.

        Notes
        -----
        An additional API call has to be made because unlike images,
        Weverse does include the URL to videos in the response for posts.
        """
        data = await self.__fetcher.fetch_video_url(video_id)
        url_mapping = {}

        for video_data in data["downloadInfo"]:
            url_mapping[int(video_data["resolution"].replace("P", ""))] = video_data[
                "url"
            ]

        return url_mapping[max(url_mapping)]

    async def fetch_notice(self, notice_id: int) -> Notice:
        """Fetches a Weverse Notice from Weverse's API using its ID.

        Parameters
        ----------
        notice_id: :class:`int`
            The notice ID of the notice to fetch.

        Returns
        -------
        :class:`.notice.Notice`
            The :class:`.notice.Notice` object of the requested Weverse Notice.

        Raises
        ------
        Forbidden
            If the signed in account has not joined the requested Weverse Community
            the notice belongs to.
        NotFound
            If the requested Weverse Notice does not exist.
        """
        data = await self.__fetcher.fetch_notice(notice_id)
        return Notice(data)

    async def fetch_member(self, member_id: str) -> Member:
        """Fetches a Weverse Member from Weverse's API using its ID.

        Parameters
        ----------
        member_id: :class:`str`
            The member ID of the member to fetch.

        Returns
        -------
        :class:`.member.Member`
            The :class:`.member.Member` object of the requested Weverse Member.

        Raises
        ------
        NotFound
            If the requested Weverse Member does not exist.
        """
        data = await self.__fetcher.fetch_member(member_id)
        return Member(data)

    async def fetch_comment(self, comment_id: str) -> Comment:
        """Fetches a Weverse Comment from Weverse's API using its ID.

        Parameters
        ----------
        comment_id: :class:`str`
            The comment ID of the comment to fetch.

        Returns
        -------
        :class:`.comment.Comment`
            The :class:`.comment.Comment` object of the requested Weverse Comment.

        Raises
        ------
        Forbidden
            If the signed in account has not joined the requested Weverse Community
            the comment belongs to.
        NotFound
            If the requested Weverse Comment does not exist.
        """
        data = await self.__fetcher.fetch_comment(comment_id)
        return Comment(data)

    async def fetch_artist_comments(self, post_id: str) -> list[Comment]:
        """Fetches a list of Weverse Artist Comments from a specific post from
        Weverse's API using the post ID.

        Parameters
        ----------
        post_id: :class:`str`
            The post ID of the post to fetch the artist comments from.

        Returns
        -------
        list[:class:`.comment.Comment`]
            The list that contains the :class:`.comment.Comment` objects of the
            Weverse Artist Comment that belong to the specified post.

        Raises
        ------
        Forbidden
            If the signed in account has not joined the requested Weverse Community
            the post belongs to.
        NotFound
            If the requested Weverse Post does not exist.
        """
        data = await self.__fetcher.fetch_artist_comments(post_id)
        data = data["data"]
        artist_comments = [Comment(comment_data) for comment_data in data]
        return artist_comments

    async def start(self) -> asyncio.Task:
        """Starts the Weverse Client."""
        await self.__fetcher.fetch_access_token()
        await self.fetch_new_notifications()  # Populates the cache.
        logger.info(
            "Started listening for Weverse Notifications. "
            "You will be updated every %s seconds.",
            self.stream_interval,
        )
        self.__task = asyncio.create_task(self.__notification_stream())
        return self.__task

    def stop(self) -> None:
        """Disconnects the Weverse Client."""
        self.__task.cancel()
        self.__task = None
        logger.info("The Weverse Client has been stopped.")

    async def __notification_stream(self) -> None:
        while True:
            try:
                await asyncio.sleep(self.stream_interval)
                notifications, comments = await self.fetch_new_notifications()

                for notification in notifications:
                    await self.on_new_notification(notification)

                    if notification.post_type == NotificationType.POST:
                        post = await self.fetch_post(notification.post_id)
                        await self.on_new_post(post)

                    elif notification.post_type == NotificationType.MOMENT:
                        moment = await self.fetch_moment(notification.post_id)
                        await self.on_new_moment(moment)

                    elif notification.post_type == NotificationType.MEDIA:
                        try:
                            media = await self.fetch_media(notification.post_id)

                        except Forbidden:
                            continue

                        await self.on_new_media(media)

                    elif notification.post_type == NotificationType.LIVE:
                        live = await self.fetch_live(notification.post_id)
                        await self.on_new_live(live)

                    elif notification.post_type == NotificationType.NOTICE:
                        if notification.community.id != 0:
                            notice = await self.fetch_notice(notification.post_id)
                            await self.on_new_notice(notice)

                for comment in comments:
                    await self.on_new_comment(comment)

            except Exception as exception:
                await self.on_exception(exception)

    async def on_new_notification(self, notification: Notification) -> None:
        """This method is called when a new notification is detected.
        You can overwrite this method to do what you want with the new
        notification.
        """

    async def on_new_post(self, post: Post) -> None:
        """This method is called when a new post is detected.
        You can overwrite this method to do what you want with the new post.
        """

    async def on_new_moment(self, moment: Moment | OldMoment) -> None:
        """This method is called when a new moment is detected.
        You can overwrite this method to do what you want with the new moment.
        """

    async def on_new_media(
        self, media: ImageMedia | WeverseMedia | YoutubeMedia
    ) -> None:
        """This method is called when a new media is detected.
        You can overwrite this method to do what you want with the new media.
        """

    async def on_new_live(self, live: Live) -> None:
        """This method is called when a new live is detected.
        You can overwrite this method to do what you want with the new live.
        """

    async def on_new_notice(self, notice: Notice) -> None:
        """This method is called when a new notice is detected.
        You can overwrite this method to do what you want with the new notice.
        """

    async def on_new_comment(self, comment: Comment) -> None:
        """This method is called when a new comment is detected.
        You can overwrite this method to do what you want with the new comment.
        """

    async def on_exception(self, exception: Exception) -> None:
        """This method is called when an unhandled exception occurs.
        You can overwrite this method to do what you want with the exception.
        By default, an exception message is logged.
        """
        logger.exception(exception)


class _WeverseCache:
    def __init__(self):
        self.cache_limit: int = 5000
        self.notification_cache: dict[int, Notification] = {}
        self.comment_notification_cache: dict[str, int] = {}
        self.comment_cache: dict[str, Comment] = {}

    def cache_comment_noti(self, comment_notification: Notification) -> None:
        """Caches comment notifications so that they can be used
        to determine how many and which comment notifications are new.

        Parameters
        ----------
        comment_notification: :class:`Notification`
            The comment notification to cache.
        """
        if len(self.comment_notification_cache) >= self.cache_limit:
            del self.comment_notification_cache[
                list(self.comment_notification_cache.keys())[0]
            ]

        self.comment_notification_cache[
            comment_notification.post_id + comment_notification.author.id
        ] = comment_notification.count

    def cache_notification(self, notification: Notification) -> None:
        """Caches notifications so that they can be used to determine which
        notifications are new.

        Parameters
        ----------
        notification: :class:`Notification`
            The notification to cache.
        """
        if len(self.notification_cache) >= self.cache_limit:
            del self.notification_cache[list(self.notification_cache.keys())[0]]

        self.notification_cache[notification.id] = notification

    def cache_comment(self, comment: Comment) -> None:
        """Caches comments so that they can be used to determine which
        comments are new.

        Parameters
        ----------
        comment: :class:`Comment`
            The comment to cache.
        """
        if len(self.comment_cache) >= self.cache_limit:
            del self.comment_cache[list(self.comment_cache.keys())[0]]

        self.comment_cache[comment.id] = comment
