# Weverse.py

Weverse.py is a Python API Wrapper that interacts with Weverse's private API.

## Intended Use

Weverse.py seeks to provide developers with a tool that allows them to make a bot that is able to retrieve Weverse Posts in semi real-time with relative ease.

## Installation

You can install Weverse.py by using a terminal of your choice, and typing `pip install weverse.py`.\
Alternatively, you can install from source by typing `pip install git+https://github.com/Anson-Quek/weverse.py.git`.

## Disclaimer

As this is my first ever serious project, coupled with my lack of necessary coding experience, I seek your understanding that there could be many aspects that are lacking.\
Any tips, advices and constructive criticisms that seeks to make this project a better project, and me a better coder will be greatly appreciated.  

## Example Usage

```python
from weverse import WeverseClient


# Create your own class that subclasses from WeverseClient
class WeverseBot(WeverseClient):
    def __init__(self, email: str, password: str):
        super().__init__(email, password)

    # This method is called every time there is a new
    # notification detected. The likelihood of you actually
    # using this method is highly unlikely as there are more
    # specialised methods that are called that should achieve
    # what you want.
    async def on_new_notification(self, notification: Notification) -> None:
        # Do what you want with the notification.
        print(notification.title)

    # This method is called every time there is a new
    # comment detected.
    async def on_new_comment(self, comment: Comment) -> None:
        # Do what you want with the comment.
        print(comment.body)

    # This method is called every time there is a new
    # post detected.
    async def on_new_post(self, post: Post) -> None:
        # Do what you want with the post.
        print(post.plain_body)

    # This method is called every time there is a new
    # media detected.
    async def on_new_media(self, media: ImageMedia | WeverseMedia | YoutubeMedia) -> None:
        # Since the media parameter will return either ImageMedia,
        # WeverseMedia or YoutubeMedia, isinstance should be used to
        # determine the type of object the media is.
        if isinstance(media, ImageMedia):
            # Do what you want with the Image Media.
            print(media.photos)

        elif isinstance(media, WeverseMedia):
            # Do what you want with the Weverse Media.
            print(media.internal_video_id)

        else:
            # Do what you want with the Youtube Media.
            print(media.youtube_url)

    # This method is called every time there is a new live
    # broadcast detected.
    async def on_new_live(self, live: Live) -> None:
        # Do what you want with the Weverse Live Broadcast.
        print(live.message_count)

    # This method is called every time there is a new notice
    # detected
    async def on_new_notice(self, notice: Notice) -> None:
        # Do what you want with the Weverse Notice.
        print(notice.photos)

    # This method is called every time there is a new moment
    # detected.
    async def on_new_moment(self, moment: Moment | OldMoment) -> None:
        # Since the moment parameter will return either Moment
        # or OldMoment, isinstance should be used to determine
        # the type of object the moment is.
        if isinstance(moment, Moment):
            # Do what you want with the Moment.
            print(moment.video)

        else:
            # Do what you want with the OldMoment. (Old Moment
            # refers to moments that were created before the Weverse
            # remake which happened somewhere in July or August)
            print(moment.photo)

if __name__ == "__main__":
    client = WeverseBot(
        email="the email of the account you want to sign in with",
        password="the password of the account you want to sign in with"
    )
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(client.start())
    loop.run_forever()

```
