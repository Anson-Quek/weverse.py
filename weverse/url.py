import base64
import hmac
import time
import urllib.parse
from hashlib import sha1

WEVERSE_KEY = "1b9cb6378d959b45714bec49971ade22e6e24e42"
BASE_API_URL = "https://global.apis.naver.com/weverse/wevweb"
API_PARAMETERS = (
    "?appId=be4d79eb8fc7bd008ee82c8ec4ff6fd4&language=en&platform=WEB&wpf=pc"
)


def get_current_epoch_time() -> int:
    """Returns the current epoch time in milli seconds."""
    return int(time.time() * 1000)


def generate_message_digest(message: bytes) -> str:
    """Generates the message digest for Weverse.

    Parameters
    ----------
    message: :class:`bytes`
        The message to generate the digest for, in bytes.

    Returns
    -------
    :class:`str`
        The message digest made URL-compatible.
    """
    key = bytes(WEVERSE_KEY, "utf-8")
    hashed = hmac.new(key=key, msg=message, digestmod=sha1)
    message_digest = base64.b64encode(hashed.digest())
    return urllib.parse.quote_plus(message_digest)


def form_request_url(url: str) -> str:
    """Forms the final URL to be used to fetch data from Weverse's API.

    Parameters
    ----------
    url: :class:`str`
        The part of the URL that is after the base API URL.

    Returns
    -------
    :class:`str`
        The final URL that can be used to interact with Weverse's API.
    """
    indexed_url = url[0:255]
    epoch_time = get_current_epoch_time()

    url_with_epoch = f"{indexed_url}{epoch_time}".encode("utf-8")

    message_digest = generate_message_digest(url_with_epoch)
    return f"{BASE_API_URL}{url}&wmsgpad={epoch_time}&wmd={message_digest}"


def latest_notifications_url() -> str:
    """The endpoint for fetching the data of the latest notifications
    from Weverse."""
    url = "/noti/feed/v1.0/activities" + API_PARAMETERS
    return form_request_url(url)


def joined_communities_url() -> str:
    """The endpoint for fetching the data from Weverse
    that contains the communities the user have joined."""
    url = "/noti/feed/v1.0/activities/community" + API_PARAMETERS
    return form_request_url(url)


def community_url(community_id: int) -> str:
    """The endpoint for fetching the data of a specified Community from Weverse."""
    url = (
        f"/community/v1.0/community-{community_id}"
        + API_PARAMETERS
        + "&fieldSet=communityHomeV1"
    )
    return form_request_url(url)


def artists_url(community_id: int) -> str:
    """The endpoint for fetching the data of the artists of a specified Community
    from Weverse."""
    url = (
        f"/member/v1.0/community-{community_id}/artistMembers"
        + API_PARAMETERS
        + "&fieldSet=artistMembersV1&fields=communityId"
        "%2CjoinedDate%2CprofileType%2CprofileName%2CprofileImageUrl"
        "%2CprofileCoverImageUrl%2CprofileComment"
    )
    return form_request_url(url)


def post_url(post_id: str) -> str:
    """The endpoint for fetching the data of a specified Post from Weverse."""
    url = f"/post/v1.0/post-{post_id}" + API_PARAMETERS + "&fieldSet=postV1"
    return form_request_url(url)


def video_url(video_id: str) -> str:
    """The endpoint for fetching the URL of videos from Weverse."""
    url = f"/cvideo/v1.0/cvideo-{video_id}/downloadInfo" + API_PARAMETERS
    return form_request_url(url)


def notice_url(notice_id: int) -> str:
    """The endpoint for fetching the data of a specified Notice from Weverse."""
    url = f"/notice/v1.0/notice-{notice_id}" + API_PARAMETERS + "&fieldSet=noticeV1"
    return form_request_url(url)


def member_url(member_id: str) -> str:
    """The endpoint for fetching the data of a specified Member from Weverse."""
    url = (
        f"/member/v1.0/member-{member_id}"
        + API_PARAMETERS
        + "&fields=memberId%2CcommunityId%2Cjoined%2CjoinedDate%2CprofileType"
        "%2CprofileName%2CprofileImageUrl%2CprofileCoverImageUrl%2CprofileComment"
        "%2Chidden%2Cblinded%2CmemberJoinStatus%2CfollowCount%2ChasMembership"
        "%2ChasOfficialMark%2CfirstJoinAt%2Cfollowed%2CartistOfficialProfile%2CmyProfile"
    )
    return form_request_url(url)


def notification_url(notification_id: int) -> str:
    """The endpoint for fetching the data of a specified Notification
    from Weverse."""
    url = "/noti/feed/v1.0/activities" + API_PARAMETERS + f"&next={notification_id+1}"
    return form_request_url(url)


def comment_url(comment_id: str) -> str:
    """The endpoint for fetching the data of a specified Comment from Weverse."""
    url = f"/comment/v1.0/comment-{comment_id}" + API_PARAMETERS + "&fieldSet=commentV1"
    return form_request_url(url)


def artist_comments_url(post_id: str) -> str:
    """The endpoint for fetching the data of the artist comments on a
    specified post from Weverse."""
    url = (
        f"/comment/v1.0/post-{post_id}/artistComments"
        + API_PARAMETERS
        + "&fieldSet=postArtistCommentsV1"
    )
    return form_request_url(url)


# No appropriate use for it as of now.
# def latest_fan_posts_url(community_id: int) -> str:
#    """The endpoint for fetching the data of the latest fan posts
#    from Weverse."""
#    url = (
#        f"/post/v1.0/community-{community_id}/feedTab"
#        + API_PARAMETERS
#        + "&fields=feedTabPosts.fieldSet%28postsV1%29.limit%2820%29%2CcontentSlots."
#        "fieldSet%28contentSlotV1%29&platform=WEB"
#    )
#    return form_request_url(url)
