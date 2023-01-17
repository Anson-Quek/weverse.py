import asyncio
import logging

from aiohttp import ClientConnectionError, ClientResponse, ClientSession
from yarl import URL

import weverse.errors
import weverse.url

from .utils import MISSING

logger = logging.getLogger("__main__")


class WeverseFetcher:
    """The Weverse Fetcher that fetches the raw data from Weverse's API.

    Attributes
    ----------
    login_payload: :class:`dict`
        The dictionary that contains the login payload to be used when
        retrieving the access token.
    """

    def __init__(self, login_payload: dict):
        self.__login_payload: dict = login_payload
        self.__access_token: str = MISSING

    @property
    def api_header(self) -> dict:
        """:class:`dict`: Returns the API headers used to communicate with Weverse."""
        return {
            "referer": "https://weverse.io",
            "authorization": f"Bearer {self.__access_token}",
        }

    async def fetch_access_token(self) -> None:
        """Retrieves the access token to be used to interact with Weverse's API.

        Raises
        ------
        LoginError
            The login credentials are invalid.
        """
        login_headers = {
            "content-type": "application/json",
            "x-acc-app-secret": "5419526f1c624b38b10787e5c10b2a7a",
            "x-acc-app-version": "abc",
            "x-acc-language": "en",
            "x-acc-service-id": "weverse",
            "x-acc-trace-id": "abc",
        }
        login_url = "https://accountapi.weverse.io/web/api/v2/auth/token/by-credentials"

        async with ClientSession() as client, client.post(
            login_url, headers=login_headers, json=self.__login_payload
        ) as resp:
            if resp.status != 200:
                raise weverse.errors.LoginError(
                    resp.status, (await resp.json()).get("message")
                )

            data = await resp.json()
            self.__access_token = data["accessToken"]
            logger.debug(
                "LOGIN SUCCESSFUL\nData: %s\nAccess Token: %s",
                data,
                self.__access_token,
            )

    async def __status_code_checker(self, response: ClientResponse) -> None:
        """Checks the response code and throws the relevant exceptions
        accordingly if the response code is not 200.

        Parameters
        ----------
        response: :class:`aiohttp.ClientResponse`
            The response to check for.

        Raises
        ------
        TokenExpired
            If the status code is 401.
        Forbidden
            If the status code is 403.
        NotFound
            If the status code is 404.
        InternalServerError
            If the status code is 500.
        RequestFailed
            If the status code is anything that is not 200, 401, 404 and 500.
        """
        if response.status == 200:
            return

        if response.status == 401:
            raise weverse.errors.TokenExpired(response.url)

        if response.status == 403:
            raise weverse.errors.Forbidden(
                response.url, (await response.json()).get("message")
            )

        if response.status == 404:
            raise weverse.errors.NotFound(response.url)

        if response.status == 500:
            raise weverse.errors.InternalServerError(response.url)

        raise weverse.errors.RequestFailed(
            response.url, response.status, (await response.json()).get("message")
        )

    async def __fetch(self, url: str) -> dict:
        """The generic fetcher that fetches data from Weverse's API.

        Parameters
        ----------
        url: :class:`str`
            The URL that is used to fetch data from.

        Returns
        -------
        :class:`dict`
            The dictionary that contains the raw data fetched from Weverse's API.
        """
        error_count = 0
        max_error_count = 3

        while error_count < max_error_count:
            try:
                async with ClientSession() as client, client.get(
                    url=URL(url, encoded=True), headers=self.api_header
                ) as resp:
                    await self.__status_code_checker(resp)
                    data = await resp.json()
                    logger.debug(
                        "RESOURCE SUCCESSFULLY FETCHED FROM WEVERSE.\nDATA: %s", data
                    )
                    return data

            except weverse.errors.TokenExpired:
                error_count += 1
                logger.warning(
                    "ACCESS TOKEN POTENTIALLY EXPIRED. "
                    "ATTEMPTING TO RENEW ACCESS TOKEN AND RETURN "
                    "REQUESTED RESOURCE SILENTLY.\n"
                    "Affected URL: %s\nError Count: %s/%s",
                    url,
                    error_count,
                    max_error_count,
                )
                await self.fetch_access_token()

            except (asyncio.exceptions.TimeoutError, ClientConnectionError):
                error_count += 1
                logger.warning(
                    "CLIENT CONNECTION ERROR ENCOUNTERED. "
                    "ATTEMPTING TO RETURN REQUESTED RESOURCE SILENTLY.\n"
                    "Affected URL: %s\nError Count: %s/%s",
                    url,
                    error_count,
                    max_error_count,
                )

            except weverse.errors.InternalServerError:
                error_count += 1
                logger.warning(
                    "TEMPORARY INTERNAL SERVER ERROR ENCOUNTERED. "
                    "ATTEMPTING TO RETURN REQUESTED RESOURCE SILENTLY.\n"
                    "Affected URL: %s\nError Count: %s/%s",
                    url,
                    error_count,
                    max_error_count,
                )

            await asyncio.sleep(1)

    async def fetch_latest_notifications(self) -> dict:
        """Retrieves the dictionary that contains the data of the latest
        Weverse notifications from Weverse's API.

        Returns
        -------
        :class:`dict`
            The dictionary that contains the data of the latest Weverse
            notifications.
        """
        return await self.__fetch(weverse.url.latest_notifications_url())

    async def fetch_notification(self, notification_id: int) -> dict:
        """Retrieves the dictionary that contains the data of the specified
        Weverse Notification from Weverse's API.

        Parameters
        ----------
        notification_id: :class:`int`
            The notification ID of the notification to fetch.

        Returns
        -------
        :class:`dict`
            The dictionary that contains the data of the specified Weverse notification.

        Raises
        ------
        NotFound
            If the requested Weverse Notification does not exist.
        """
        url = weverse.url.notification_url(notification_id)
        data = await self.__fetch(url)

        if not data["data"] or not data["data"][0].get("community"):
            raise weverse.errors.NotFound(url)

        return data["data"][0]

    async def fetch_joined_communities(self) -> dict:
        """Retrieves the dictionary that contains the data of the joined
        communities the account has access to, from Weverse's API.

        Returns
        -------
        :class:`dict`
            The dictionary that contains the data of the joined communities.
        """
        return await self.__fetch(weverse.url.joined_communities_url())

    async def fetch_community(self, community_id: int) -> dict:
        """Retrieves the dictionary that contains the data of the specified
        Weverse Community from Weverse's API.

        Parameters
        ----------
        community_id: :class:`int`
            The community ID of the community to fetch.

        Returns
        -------
        :class:`dict`
            The dictionary that contains the data of the specified Weverse community.

        Raises
        ------
        Forbidden
            If the signed in account has not joined the requested Weverse Community.
        NotFound
            If the requested Weverse Community does not exist.
        """
        return await self.__fetch(weverse.url.community_url(community_id))

    async def fetch_artists(self, community_id: int) -> dict:
        """Retrieves the dictionary that contains the data of the artists
        that belong to the specified Weverse Community from Weverse's API.

        Parameters
        ----------
        community_id: :class:`int`
            The community ID of the community to fetch the artists' data from.

        Returns
        -------
        :class:`dict`
            The dictionary that contains the data of the artists of the specified
            Weverse community.

        Raises
        ------
        Forbidden
            If the signed in account has not joined the requested Weverse Community.
        NotFound
            If the requested Weverse Community does not exist.
        """
        return await self.__fetch(weverse.url.artists_url(community_id))

    async def fetch_post(self, post_id: str) -> dict:
        """Retrieves the dictionary that contains the data of the specified
        Weverse Post from Weverse's API.

        Parameters
        ----------
        post_id: :class:`str`
            The post ID of the post to fetch.

        Returns
        -------
        :class:`dict`
            The dictionary that contains the data of the specified Weverse post.

        Raises
        ------
        Forbidden
            If the signed in account has not joined the requested Weverse Community
            the post belongs to.
        NotFound
            If the requested Weverse Post does not exist.
        """
        return await self.__fetch(weverse.url.post_url(post_id))

    async def fetch_video_url(self, video_id: str) -> dict:
        """Fetches a Weverse Post Video URL by its ID.

        Parameters
        ----------
        video_id: :class:`str`
            The ID of the video to fetch.

        Returns
        -------
        :class:`dict`
            The dictionary that contains the data of the specified Weverse video.
        """
        return await self.__fetch(weverse.url.video_url(video_id))

    async def fetch_notice(self, notice_id: int) -> dict:
        """Retrieves the dictionary that contains the data of the specified
        Weverse Notice from Weverse's API.

        Parameters
        ----------
        notice_id: :class:`int`
            The notice ID of the notice to fetch.

        Returns
        -------
        :class:`dict`
            The dictionary that contains the data of the specified Weverse notice.

        Raises
        ------
        Forbidden
            If the signed in account has not joined the requested Weverse Community
            the notice belongs to.
        NotFound
            If the requested Weverse Notice does not exist.
        """
        url = weverse.url.notice_url(notice_id)
        data = await self.__fetch(url)

        if "parentId" not in data:
            raise weverse.errors.NotFound(url)

        return data

    async def fetch_member(self, member_id: str) -> dict:
        """Retrieves the dictionary that contains the data of the specified
        Weverse Member from Weverse's API.

        Parameters
        ----------
        member_id: :class:`str`
            The member ID of the member to fetch.

        Returns
        -------
        :class:`dict`
            The dictionary that contains the data of the specified Weverse member.

        Raises
        ------
        NotFound
            If the requested Weverse Member does not exist.
        """
        return await self.__fetch(weverse.url.member_url(member_id))

    async def fetch_comment(self, comment_id: str) -> dict:
        """Retrieves the dictionary that contains the data of the specified
        Weverse Comment from Weverse's API.

        Parameters
        ----------
        comment_id: :class:`str`
            The comment ID of the comment to fetch.

        Returns
        -------
        :class:`dict`
            The dictionary that contains the data of the specified Weverse comment.

        Raises
        ------
        Forbidden
            If the signed in account has not joined the requested Weverse Community
            the comment belongs to.
        NotFound
            If the requested Weverse Comment does not exist.
        """
        return await self.__fetch(weverse.url.comment_url(comment_id))

    async def fetch_artist_comments(self, post_id: str) -> dict:
        """Retrieves the dictionary that contains the data of the artist comments
        that belong to the specified Weverse Post from Weverse's API.

        Parameters
        ----------
        post_id: :class:`str`
            The post ID of the post to fetch the artist comments' data from.

        Returns
        -------
        :class:`dict`
            The dictionary that contains the data of the artist comments of the
            specified Weverse post.

        Raises
        ------
        Forbidden
            If the signed in account has not joined the requested Weverse Community
            the post belongs to.
        NotFound
            If the requested Weverse Post does not exist.
        """
        return await self.__fetch(weverse.url.artist_comments_url(post_id))
