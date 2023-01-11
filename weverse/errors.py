class WeverseException(Exception):
    """Base exception class that other Weverse exceptions inherit from."""


class LoginError(WeverseException):
    """An Exception raised when the login to Weverse fails."""

    def __init__(self, code: int, reason: str):
        message = f"Login to Weverse has failed.\nCode: {code}\nReason: {reason}"
        super().__init__(message)


class RequestFailed(WeverseException):
    """An Exception raised when the status code of the response returned by the
    API is not 200, 401, 403, 404 or 500. (Note: This is because 401, 403, 404
    and 500 has their own specific exceptions.)"""

    def __init__(self, url: str, code: int, reason: str):
        message = f"Request to {url} has failed.\nCode: {code}\nReason: {reason}."
        super().__init__(message)


class TokenExpired(WeverseException):
    """An Exception raised when the status code of the response returned by the
    API is 401."""

    def __init__(self, url: str):
        message = (
            f"Request to {url} has failed.\nCode: 401\n\n"
            "Reason: The access token has potentially expired."
        )
        super().__init__(message)


class Forbidden(WeverseException):
    """An Exception raised when the status code of the response returned by the
    API is 403."""

    def __init__(self, url: str, reason: str):
        message = f"Request to {url} has failed.\nCode: 403\nReason: {reason}."
        super().__init__(message)


class NotFound(WeverseException):
    """An Exception raised when the status code of the response returned by the
    API is 404."""

    def __init__(self, url: str):
        message = (
            f"Request to {url} has failed.\nCode: 404\n"
            "Reason: The requested resource cannot be found or does not exist."
        )
        super().__init__(message)


class InternalServerError(WeverseException):
    """An Exception raised when the status code of the response returned by the
    API is 500."""

    def __init__(self, url: str):
        message = (
            f"Request to {url} has failed.\nCode: 500\n\n"
            "Reason: The Weverse API encountered an Internal Server Error."
        )
        super().__init__(message)
